// Initialize Pi SDK
const Pi = window.Pi;
let piSDK = null;

// Store workflow data
let workflowNodes = [];
let workflowConnections = [];
let currentNodeId = 1;
let selectedNode = null;
let offsetX = 0, offsetY = 0;
let isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
let isDragging = false;
let connectingNode = null;
let connectionSource = null;
let currentWorkflow = {
    id: null,
    name: "New Workflow",
    nodes: [],
    connections: []
};

// Sample data for demonstration
const sampleWorkflows = [
    {
        id: "wf-1",
        name: "Email Automation",
        description: "Sends automated emails based on user actions",
        status: "active",
        lastRun: "2 hours ago",
        icon: "fas fa-envelope",
        iconColor: "#4f46e5"
    },
    {
        id: "wf-2",
        name: "E-commerce Sync",
        description: "Syncs orders between Shopify and database",
        status: "active",
        lastRun: "5 minutes ago",
        icon: "fas fa-shopping-cart",
        iconColor: "#0e9f6e"
    },
    {
        id: "wf-3",
        name: "Notification System",
        description: "Sends push notifications for important events",
        status: "paused",
        lastRun: "2 days ago",
        icon: "fas fa-bell",
        iconColor: "#f59e0b"
    }
];

const sampleTools = [
    {
        id: "tool-1",
        name: "Database Operations",
        description: "Create, read, update and delete database records",
        category: "data",
        icon: "fas fa-database",
        iconColor: "#8b5cf6",
        uses: "200+"
    },
    {
        id: "tool-2",
        name: "Webhook",
        description: "Trigger workflows from external applications",
        category: "app",
        icon: "fas fa-code",
        iconColor: "#ec4899",
        uses: "150+"
    },
    {
        id: "tool-3",
        name: "Pi Network Integration",
        description: "Connect with Pi blockchain and user authentication",
        category: "pi",
        icon: "fab fa-pi",
        iconColor: "#14bca8",
        uses: "Pi Ecosystem"
    }
];

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    // Check if we have a stored session
    const userSession = localStorage.getItem('piUserSession');
    if (userSession) {
        try {
            const sessionData = JSON.parse(userSession);
            if (sessionData.authenticated && sessionData.expires > Date.now()) {
                // User is already authenticated
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('appContainer').style.display = 'flex';
                updateUIWithUserData(sessionData.user);
                loadSampleData();
            }
        } catch (e) {
            console.error('Error parsing stored session', e);
            localStorage.removeItem('piUserSession');
        }
    }

    // Initialize Pi SDK
    try {
        piSDK = Pi.init({ version: "2.0" });
        console.log('Pi SDK initialized successfully');
    } catch (error) {
        console.error('Failed to initialize Pi SDK', error);
    }

    // Show mobile menu toggle on mobile devices
    if (isMobile) {
        document.getElementById('mobileMenuToggle').style.display = 'flex';
    }

    // Initialize event listeners
    initEventListeners();
    
    // Initialize node dragging
    initNodeDragging();
});

// Initialize all event listeners
function initEventListeners() {
    // Login functionality
    document.getElementById('loginBtn').addEventListener('click', handleLogin);
    document.getElementById('piLoginBtn').addEventListener('click', authenticateWithPi);
    document.getElementById('signUpLink').addEventListener('click', handleSignUp);
    
    // Navigation
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', handleMenuNavigation);
    });
    
    // Header actions
    document.getElementById('connectPiBtn').addEventListener('click', showPiConnectModal);
    document.getElementById('newWorkflowBtn').addEventListener('click', createNewWorkflow);
    document.getElementById('helpBtn').addEventListener('click', showHelp);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    
    // Editor actions
    document.getElementById('saveWorkflowBtn').addEventListener('click', saveWorkflow);
    document.getElementById('executeWorkflowBtn').addEventListener('click', executeWorkflow);
    
    // Modal actions
    document.querySelector('.close-modal').addEventListener('click', hidePiConnectModal);
    document.getElementById('piAuthOption').addEventListener('click', () => addNodeToCanvas('pi-auth'));
    document.getElementById('piPaymentOption').addEventListener('click', () => addNodeToCanvas('pi-payment'));
    document.getElementById('piDataOption').addEventListener('click', () => addNodeToCanvas('pi-data'));
    
    // Mobile menu toggle
    document.getElementById('mobileMenuToggle').addEventListener('click', toggleMobileMenu);
    
    // Search functionality
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    
    // Filter and sort buttons
    document.getElementById('filterBtn').addEventListener('click', showFilterOptions);
    document.getElementById('sortBtn').addEventListener('click', showSortOptions);
}

// Load sample data for demonstration
function loadSampleData() {
    renderWorkflows(sampleWorkflows);
    renderTools(sampleTools);
}

// Render workflow cards
function renderWorkflows(workflows) {
    const workflowsGrid = document.getElementById('workflowsGrid');
    workflowsGrid.innerHTML = '';
    
    workflows.forEach(workflow => {
        const workflowCard = document.createElement('div');
        workflowCard.className = 'card';
        workflowCard.innerHTML = `
            <div class="card-header">
                <div class="card-icon" style="background-color: rgba(${hexToRgb(workflow.iconColor)}, 0.1); color: ${workflow.iconColor};">
                    <i class="${workflow.icon}"></i>
                </div>
                <span class="badge ${workflow.status === 'active' ? 'badge-success' : 'badge-warning'}">${workflow.status}</span>
            </div>
            <h3 class="card-title">${workflow.name}</h3>
            <p class="card-desc">${workflow.description}</p>
            <div class="card-actions">
                <span class="text-xs">Last run: ${workflow.lastRun}</span>
                <button class="btn btn-outline" data-workflow-id="${workflow.id}">Edit</button>
            </div>
        `;
        workflowsGrid.appendChild(workflowCard);
    });
    
    // Add event listeners to edit buttons
    document.querySelectorAll('[data-workflow-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const workflowId = this.getAttribute('data-workflow-id');
            openWorkflow(workflowId);
        });
    });
}

// Render tool cards
function renderTools(tools) {
    const toolsGrid = document.getElementById('toolsGrid');
    toolsGrid.innerHTML = '';
    
    tools.forEach(tool => {
        const toolCard = document.createElement('div');
        toolCard.className = 'card';
        toolCard.innerHTML = `
            <div class="card-header">
                <div class="card-icon" style="background-color: rgba(${hexToRgb(tool.iconColor)}, 0.1); color: ${tool.iconColor};">
                    <i class="${tool.icon}"></i>
                </div>
                ${tool.category === 'pi' ? '<span class="badge badge-pi">Pi Network</span>' : ''}
            </div>
            <h3 class="card-title">${tool.name}</h3>
            <p class="card-desc">${tool.description}</p>
            <div class="card-actions">
                <span class="text-xs">${tool.uses} uses</span>
                <button class="btn btn-outline" data-tool-id="${tool.id}">Add to workflow</button>
            </div>
        `;
        toolsGrid.appendChild(toolCard);
    });
    
    // Add event listeners to add buttons
    document.querySelectorAll('[data-tool-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const toolId = this.getAttribute('data-tool-id');
            addToolToWorkflow(toolId);
        });
    });
}

// Convert hex color to RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? 
        `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` 
        : '0, 0, 0';
}

// Handle login
function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    if (email && password) {
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('appContainer').style.display = 'flex';
        loadSampleData();
    } else {
        alert('Please enter both email and password');
    }
}

// Handle sign up
function handleSignUp(e) {
    e.preventDefault();
    alert('Sign up functionality would be implemented here');
}

// Handle menu navigation
function handleMenuNavigation() {
    const view = this.getAttribute('data-view');
    if (view) {
        // Hide all views
        document.querySelectorAll('.dashboard, .workflow-editor').forEach(el => {
            el.style.display = 'none';
        });
        
        // Show selected view
        document.getElementById(view).style.display = view === 'editorView' ? 'flex' : 'block';
        
        // Update active menu item
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
        
        // On mobile, close sidebar after selection
        if (isMobile) {
            document.querySelector('.sidebar').classList.remove('mobile-open');
        }
    }
}

// Show Pi Connect modal
function showPiConnectModal() {
    document.getElementById('piConnectModal').style.display = 'flex';
}

// Hide Pi Connect modal
function hidePiConnectModal() {
    document.getElementById('piConnectModal').style.display = 'none';
}

// Create new workflow
function createNewWorkflow() {
    // Reset current workflow
    currentWorkflow = {
        id: 'wf-' + Date.now(),
        name: 'New Workflow',
        nodes: [],
        connections: []
    };
    
    // Clear canvas
    document.getElementById('workflowCanvas').innerHTML = '';
    workflowNodes = [];
    workflowConnections = [];
    
    // Update UI
    document.getElementById('workflowTitle').textContent = currentWorkflow.name;
    
    // Switch to editor view
    document.getElementById('dashboardView').style.display = 'none';
    document.getElementById('editorView').style.display = 'flex';
    
    // Update menu
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector('[data-view="editorView"]').classList.add('active');
    
    // On mobile, close sidebar
    if (isMobile) {
        document.querySelector('.sidebar').classList.remove('mobile-open');
    }
}

// Open existing workflow
function openWorkflow(workflowId) {
    // In a real app, this would load the workflow from storage
    // For now, we'll just create a new one
    createNewWorkflow();
    
    // Set the workflow name
    const workflow = sampleWorkflows.find(w => w.id === workflowId);
    if (workflow) {
        currentWorkflow.name = workflow.name;
        document.getElementById('workflowTitle').textContent = workflow.name;
    }
}

// Add tool to workflow
function addToolToWorkflow(toolId) {
    // In a real app, this would map tool IDs to node types
    // For now, we'll use a simple mapping
    const toolToNodeMap = {
        'tool-1': 'set', // Database Operations -> Set node
        'tool-2': 'webhook', // Webhook -> Webhook node
        'tool-3': 'pi-auth' // Pi Network Integration -> Pi Auth node
    };
    
    const nodeType = toolToNodeMap[toolId];
    if (nodeType) {
        // Switch to editor view if not already there
        document.getElementById('dashboardView').style.display = 'none';
        document.getElementById('editorView').style.display = 'flex';
        
        // Add the node
        addNodeToCanvas(nodeType);
    }
}

// Save workflow
function saveWorkflow() {
    // Update workflow data with current nodes and connections
    currentWorkflow.nodes = workflowNodes;
    currentWorkflow.connections = workflowConnections;
    
    // In a real app, this would save to a backend
    // For now, we'll just show a confirmation
    alert(`Workflow "${currentWorkflow.name}" saved successfully!`);
}

// Execute workflow
function executeWorkflow() {
    if (workflowNodes.length === 0) {
        alert('Please add at least one node to the workflow');
        return;
    }
    
    // Find start nodes (triggers)
    const startNodes = workflowNodes.filter(node => node.category === 'trigger');
    
    if (startNodes.length === 0) {
        alert('Please add a trigger node to start the workflow');
        return;
    }
    
    // Simulate workflow execution
    simulateWorkflowExecution();
}

// Simulate workflow execution with visual feedback
function simulateWorkflowExecution() {
    const nodes = document.querySelectorAll('.node');
    let delay = 0;
    
    // Reset all nodes
    nodes.forEach(node => {
        node.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.05)';
    });
    
    // Animate each node with a delay
    workflowNodes.forEach((node, index) => {
        const nodeElement = document.querySelector(`[data-node-id="${node.id}"]`);
        
        setTimeout(() => {
            nodeElement.style.boxShadow = '0 0 0 2px var(--success)';
            
            // Reset after a moment
            setTimeout(() => {
                nodeElement.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.05)';
            }, 500);
        }, delay);
        
        delay += 800;
    });
    
    // Show completion message
    setTimeout(() => {
        alert('Workflow executed successfully!');
    }, delay);
}

// Show help
function showHelp() {
    alert('Help documentation would be displayed here');
}

// Handle logout
function handleLogout() {
    localStorage.removeItem('piUserSession');
    document.getElementById('appContainer').style.display = 'none';
    document.getElementById('loginScreen').style.display = 'flex';
}

// Toggle mobile menu
function toggleMobileMenu() {
    document.querySelector('.sidebar').classList.toggle('mobile-open');
}

// Handle search
function handleSearch() {
    const searchTerm = this.value.toLowerCase();
    
    // Filter workflows
    const filteredWorkflows = sampleWorkflows.filter(workflow => 
        workflow.name.toLowerCase().includes(searchTerm) || 
        workflow.description.toLowerCase().includes(searchTerm)
    );
    
    // Filter tools
    const filteredTools = sampleTools.filter(tool => 
        tool.name.toLowerCase().includes(searchTerm) || 
        tool.description.toLowerCase().includes(searchTerm)
    );
    
    // Render filtered results
    renderWorkflows(filteredWorkflows);
    renderTools(filteredTools);
}

// Show filter options
function showFilterOptions() {
    alert('Filter options would be displayed here');
}

// Show sort options
function showSortOptions() {
    alert('Sort options would be displayed here');
}

// Initialize node dragging from palette
function initNodeDragging() {
    const nodeItems = document.querySelectorAll('.node-item');
    
    nodeItems.forEach(item => {
        item.addEventListener('dragstart', function(e) {
            const nodeType = this.getAttribute('data-type');
            e.dataTransfer.setData('nodeType', nodeType);
        });
        
        // For touch devices, add long press to drag
        if (isMobile) {
            let pressTimer;
            
            item.addEventListener('touchstart', function(e) {
                pressTimer = setTimeout(function() {
                    const nodeType = item.getAttribute('data-type');
                    const touch = e.touches[0];
                    addNodeToCanvas(nodeType, touch.clientX, touch.clientY);
                }, 500); // 500ms long press
            });
            
            item.addEventListener('touchend', function() {
                clearTimeout(pressTimer);
            });
            
            item.addEventListener('touchmove', function() {
                clearTimeout(pressTimer);
            });
        }
    });

    const canvas = document.getElementById('workflowCanvas');
    
    canvas.addEventListener('dragover', function(e) {
        e.preventDefault();
        // Show drop indicator
        canvas.style.backgroundColor = 'rgba(236, 240, 241, 0.5)';
    });
    
    canvas.addEventListener('dragleave', function(e) {
        // Reset canvas background
        canvas.style.backgroundColor = '';
    });
    
    canvas.addEventListener('drop', function(e) {
        e.preventDefault();
        // Reset canvas background
        canvas.style.backgroundColor = '';
        
        const nodeType = e.dataTransfer.getData('nodeType');
        if (nodeType) {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            addNodeToCanvas(nodeType, x, y);
        }
    });
    
    // Touch events for mobile
    if (isMobile) {
        canvas.addEventListener('touchmove', function(e) {
            if (selectedNode && e.touches.length === 1) {
                e.preventDefault();
                const touch = e.touches[0];
                const x = touch.clientX - offsetX;
                const y = touch.clientY - offsetY;
                
                selectedNode.style.left = x + 'px';
                selectedNode.style.top = y + 'px';
            }
        }, { passive: false });
        
        canvas.addEventListener('touchend', function() {
            if (selectedNode) {
                selectedNode.classList.remove('node-moving');
                selectedNode = null;
                
                // Update node position in data model
                const nodeId = selectedNode.getAttribute('data-node-id');
                const nodeIndex = workflowNodes.findIndex(n => n.id === nodeId);
                if (nodeIndex !== -1) {
                    workflowNodes[nodeIndex].x = parseInt(selectedNode.style.left || '0');
                    workflowNodes[nodeIndex].y = parseInt(selectedNode.style.top || '0');
                }
            }
        });
    }
}

// Make nodes draggable
function makeNodeDraggable(node) {
    const header = node.querySelector('.node-header');
    
    // Mouse events
    header.addEventListener('mousedown', function(e) {
        startDrag(e, node);
    });
    
    // Touch events for mobile
    if (isMobile) {
        header.addEventListener('touchstart', function(e) {
            if (e.touches.length === 1) {
                const touch = e.touches[0];
                const dragEvent = {
                    clientX: touch.clientX,
                    clientY: touch.clientY,
                    preventDefault: () => e.preventDefault()
                };
                startDrag(dragEvent, node);
            }
        });
    }
    
    // Setup connection points
    const inputPoint = node.querySelector('.input-point');
    const outputPoint = node.querySelector('.output-point');
    
    if (inputPoint) {
        inputPoint.addEventListener('mousedown', function(e) {
            e.stopPropagation();
            startConnection(node, 'input');
        });
        
        if (isMobile) {
            inputPoint.addEventListener('touchstart', function(e) {
                e.stopPropagation();
                startConnection(node, 'input');
            });
        }
    }
    
    if (outputPoint) {
        outputPoint.addEventListener('mousedown', function(e) {
            e.stopPropagation();
            startConnection(node, 'output');
        });
        
        if (isMobile) {
            outputPoint.addEventListener('touchstart', function(e) {
                e.stopPropagation();
                startConnection(node, 'output');
            });
        }
    }
    
    // Prevent text selection while dragging
    header.addEventListener('selectstart', function(e) {
        e.preventDefault();
        return false;
    });
}

// Start drag function
function startDrag(e, node) {
    e.preventDefault();
    
    selectedNode = node;
    const rect = node.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
    
    // Add moving class for visual feedback
    node.classList.add('node-moving');
    
    function onMouseMove(e) {
        if (!selectedNode) return;
        
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        
        // Update node position
        node.style.left = x + 'px';
        node.style.top = y + 'px';
        
        // Update connections if any
        updateNodeConnections(node);
    }
    
    function onMouseUp() {
        if (!selectedNode) return;
        
        // Remove moving class
        node.classList.remove('node-moving');
        
        selectedNode = null;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        document.removeEventListener('mouseleave', onMouseUp);
        
        // Update node position in data model
        const nodeId = node.getAttribute('data-node-id');
        const nodeIndex = workflowNodes.findIndex(n => n.id === nodeId);
        if (nodeIndex !== -1) {
            workflowNodes[nodeIndex].x = parseInt(node.style.left || '0');
            workflowNodes[nodeIndex].y = parseInt(node.style.top || '0');
        }
    }
    
    // Add event listeners for mouse
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mouseleave', onMouseUp);
}

// Start connection between nodes
function startConnection(node, type) {
    connectingNode = node;
    connectionSource = type;
    
    // Visual feedback
    node.classList.add('node-connecting');
    
    // Create temporary connection line
    const canvas = document.getElementById('workflowCanvas');
    const connectionLine = document.createElement('div');
    connectionLine.className = 'connection';
    connectionLine.id = 'temp-connection';
    canvas.appendChild(connectionLine);
    
    // Update connection line on mouse move
    function updateConnectionLine(e) {
        if (!connectingNode) return;
        
        const nodeRect = connectingNode.getBoundingClientRect();
        const canvasRect = canvas.getBoundingClientRect();
        
        let startX, startY, endX, endY;
        
        if (connectionSource === 'output') {
            const outputPoint = connectingNode.querySelector('.output-point');
            const outputRect = outputPoint.getBoundingClientRect();
            
            startX = outputRect.left - canvasRect.left + outputRect.width / 2;
            startY = outputRect.top - canvasRect.top + outputRect.height / 2;
            endX = e.clientX - canvasRect.left;
            endY = e.clientY - canvasRect.top;
        } else {
            const inputPoint = connectingNode.querySelector('.input-point');
            const inputRect = inputPoint.getBoundingClientRect();
            
            startX = inputRect.left - canvasRect.left + inputRect.width / 2;
            startY = inputRect.top - canvasRect.top + inputRect.height / 2;
            endX = e.clientX - canvasRect.left;
            endY = e.clientY - canvasRect.top;
        }
        
        // Draw line
        drawConnectionLine(connectionLine, startX, startY, endX, endY);
    }
    
    // Finish connection
    function finishConnection(e) {
        if (!connectingNode) return;
        
        // Find node under mouse
        const nodes = document.querySelectorAll('.node');
        let targetNode = null;
        let targetType = null;
        
        nodes.forEach(node => {
            if (node !== connectingNode) {
                const rect = node.getBoundingClientRect();
                if (e.clientX >= rect.left && e.clientX <= rect.right &&
                    e.clientY >= rect.top && e.clientY <= rect.bottom) {
                    targetNode = node;
                    
                    // Check if mouse is over input or output point
                    const inputPoint = node.querySelector('.input-point');
                    const outputPoint = node.querySelector('.output-point');
                    
                    if (inputPoint) {
                        const inputRect = inputPoint.getBoundingClientRect();
                        if (e.clientX >= inputRect.left && e.clientX <= inputRect.right &&
                            e.clientY >= inputRect.top && e.clientY <= inputRect.bottom) {
                            targetType = 'input';
                        }
                    }
                    
                    if (outputPoint && !targetType) {
                        const outputRect = outputPoint.getBoundingClientRect();
                        if (e.clientX >= outputRect.left && e.clientX <= outputRect.right &&
                            e.clientY >= outputRect.top && e.clientY <= outputRect.bottom) {
                            targetType = 'output';
                        }
                    }
                }
            }
        });
        
        // If valid connection
        if (targetNode && targetType && targetType !== connectionSource) {
            createConnection(connectingNode, targetNode, connectionSource, targetType);
        }
        
        // Clean up
        connectingNode.classList.remove('node-connecting');
        document.removeEventListener('mousemove', updateConnectionLine);
        document.removeEventListener('mouseup', finishConnection);
        document.removeEventListener('click', finishConnection);
        
        const tempConnection = document.getElementById('temp-connection');
        if (tempConnection) {
            tempConnection.remove();
        }
        
        connectingNode = null;
        connectionSource = null;
    }
    
    // Add event listeners
    document.addEventListener('mousemove', updateConnectionLine);
    document.addEventListener('mouseup', finishConnection);
    document.addEventListener('click', finishConnection);
}

// Draw connection line between points
function drawConnectionLine(lineElement, x1, y1, x2, y2) {
    // Calculate line properties
    const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
    
    // Position and transform line
    lineElement.style.width = length + 'px';
    lineElement.style.left = x1 + 'px';
    lineElement.style.top = y1 + 'px';
    lineElement.style.transform = `rotate(${angle}deg)`;
    lineElement.style.transformOrigin = '0 0';
}

// Create connection between nodes
function createConnection(sourceNode, targetNode, sourceType, targetType) {
    const sourceId = sourceNode.getAttribute('data-node-id');
    const targetId = targetNode.getAttribute('data-node-id');
    
    // Check if connection already exists
    const existingConnection = workflowConnections.find(conn => 
        conn.sourceId === sourceId && conn.targetId === targetId &&
        conn.sourceType === sourceType && conn.targetType === targetType
    );
    
    if (existingConnection) {
        return; // Connection already exists
    }
    
    // Add to connections array
    workflowConnections.push({
        id: 'conn-' + Date.now(),
        sourceId: sourceId,
        targetId: targetId,
        sourceType: sourceType,
        targetType: targetType
    });
    
    // Create visual connection
    createVisualConnection(sourceNode, targetNode, sourceType, targetType);
}

// Create visual connection between nodes
function createVisualConnection(sourceNode, targetNode, sourceType, targetType) {
    const canvas = document.getElementById('workflowCanvas');
    const connectionLine = document.createElement('div');
    connectionLine.className = 'connection';
    
    // Get connection points
    const sourcePoint = sourceType === 'output' ? 
        sourceNode.querySelector('.output-point') : 
        sourceNode.querySelector('.input-point');
    
    const targetPoint = targetType === 'output' ? 
        targetNode.querySelector('.output-point') : 
        targetNode.querySelector('.input-point');
    
    // Calculate positions
    const canvasRect = canvas.getBoundingClientRect();
    const sourceRect = sourcePoint.getBoundingClientRect();
    const targetRect = targetPoint.getBoundingClientRect();
    
    const startX = sourceRect.left - canvasRect.left + sourceRect.width / 2;
    const startY = sourceRect.top - canvasRect.top + sourceRect.height / 2;
    const endX = targetRect.left - canvasRect.left + targetRect.width / 2;
    const endY = targetRect.top - canvasRect.top + targetRect.height / 2;
    
    // Draw line
    drawConnectionLine(connectionLine, startX, startY, endX, endY);
    
    // Add to canvas
    canvas.appendChild(connectionLine);
    
    // Store reference to connection element
    const connectionId = 'conn-' + Date.now();
    connectionLine.id = connectionId;
    
    // Add connection points
    addConnectionPoints(connectionLine, startX, startY, endX, endY);
}

// Add connection points to line
function addConnectionPoints(connectionLine, x1, y1, x2, y2) {
    // Create start point
    const startPoint = document.createElement('div');
    startPoint.className = 'connection-point';
    startPoint.style.left = (x1 - 8) + 'px';
    startPoint.style.top = (y1 - 8) + 'px';
    
    // Create end point
    const endPoint = document.createElement('div');
    endPoint.className = 'connection-point';
    endPoint.style.left = (x2 - 8) + 'px';
    endPoint.style.top = (y2 - 8) + 'px';
    
    // Add to canvas
    const canvas = document.getElementById('workflowCanvas');
    canvas.appendChild(startPoint);
    canvas.appendChild(endPoint);
    
    // Make points draggable to modify connection
    makeConnectionPointDraggable(startPoint, connectionLine, true);
    makeConnectionPointDraggable(endPoint, connectionLine, false);
}

// Make connection points draggable
function makeConnectionPointDraggable(point, connectionLine, isStartPoint) {
    point.addEventListener('mousedown', function(e) {
        e.stopPropagation();
        dragConnectionPoint(point, connectionLine, isStartPoint);
    });
}

// Drag connection point
function dragConnectionPoint(point, connectionLine, isStartPoint) {
    const canvas = document.getElementById('workflowCanvas');
    const canvasRect = canvas.getBoundingClientRect();
    
    let offsetX = 0;
    let offsetY = 0;
    
    function onMouseMove(e) {
        const x = e.clientX - canvasRect.left - offsetX;
        const y = e.clientY - canvasRect.top - offsetY;
        
        // Update point position
        point.style.left = (x - 8) + 'px';
        point.style.top = (y - 8) + 'px';
        
        // Update connection line
        if (isStartPoint) {
            const endX = parseFloat(point.style.left) + 8;
            const endY = parseFloat(point.style.top) + 8;
            // Would need to get the other end point position
            // This is a simplified implementation
        } else {
            // Similar logic for end point
        }
    }
    
    function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    }
    
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
}

// Update connections when node moves
function updateNodeConnections(node) {
    const nodeId = node.getAttribute('data-node-id');
    const connections = workflowConnections.filter(conn => 
        conn.sourceId === nodeId || conn.targetId === nodeId
    );
    
    connections.forEach(conn => {
        const connectionElement = document.getElementById(conn.id);
        if (connectionElement) {
            const sourceNode = document.querySelector(`[data-node-id="${conn.sourceId}"]`);
            const targetNode = document.querySelector(`[data-node-id="${conn.targetId}"]`);
            
            if (sourceNode && targetNode) {
                const sourcePoint = conn.sourceType === 'output' ? 
                    sourceNode.querySelector('.output-point') : 
                    sourceNode.querySelector('.input-point');
                
                const targetPoint = conn.targetType === 'output' ? 
                    targetNode.querySelector('.output-point') : 
                    targetNode.querySelector('.input-point');
                
                const canvas = document.getElementById('workflowCanvas');
                const canvasRect = canvas.getBoundingClientRect();
                const sourceRect = sourcePoint.getBoundingClientRect();
                const targetRect = targetPoint.getBoundingClientRect();
                
                const startX = sourceRect.left - canvasRect.left + sourceRect.width / 2;
                const startY = sourceRect.top - canvasRect.top + sourceRect.height / 2;
                const endX = targetRect.left - canvasRect.left + targetRect.width / 2;
                const endY = targetRect.top - canvasRect.top + targetRect.height / 2;
                
                drawConnectionLine(connectionElement, startX, startY, endX, endY);
            }
        }
    });
}

// Add a node to the canvas
function addNodeToCanvas(nodeType, x = 100, y = 100) {
    const canvas = document.getElementById('workflowCanvas');
    const nodeId = 'node-' + currentNodeId++;
    
    // Adjust for scroll position on mobile
    if (isMobile) {
        const canvasRect = canvas.getBoundingClientRect();
        x = x - canvasRect.left;
        y = y - canvasRect.top;
    }
    
    let nodeHtml = '';
    let nodeTitle = '';
    let nodeCategory = '';
    let nodeIcon = '';
    
    // Define node templates
    const nodeTemplates = {
        'schedule': {
            title: 'Schedule Trigger',
            category: 'trigger',
            icon: 'fas fa-clock',
            html: `
                <div class="node node-trigger" data-node-id="${nodeId}" style="left: ${x}px; top: ${y}px;">
                    <div class="node-header">
                        <span><i class="fas fa-clock"></i> Schedule</span>
                        <i class="fas fa-grip-vertical"></i>
                    </div>
                    <div class="node-content">
                        <div class="form-group">
                            <label>Frequency</label>
                            <select>
                                <option value="minutes">Minutes</option>
                                <option value="hours">Hours</option>
                                <option value="days">Days</option>
                                <option value="weeks">Weeks</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Interval</label>
                            <input type="number" value="1" min="1">
                        </div>
                        <div class="node-io">
                            <div class="input-point"></div>
                            <div class="output-point"></div>
                        </div>
                    </div>
                </div>
            `
        },
        'webhook': {
            title: 'Webhook Trigger',
            category: 'trigger',
            icon: 'fas fa-code-branch',
            html: `
                <div class="node node-trigger" data-node-id="${nodeId}" style="left: ${x}px; top: ${y}px;">
                    <div class="node-header">
                        <span><i class="fas fa-code-branch"></i> Webhook</span>
                        <i class="fas fa-grip-vertical"></i>
                    </div>
                    <div class="node-content">
                        <div class="form-group">
                            <label>Webhook URL</label>
                            <input type="text" value="/webhook/${Math.random().toString(36).substring(2, 10)}" readonly>
                        </div>
                        <div class="form-group">
                            <label>HTTP Method</label>
                            <select>
                                <option value="POST">POST</option>
                                <option value="GET">GET</option>
                                <option value="PUT">PUT</option>
                            </select>
                        </div>
                        <div class="node-io">
                            <div class="input-point"></div>
                            <div class="output-point"></div>
                        </div>
                    </div>
                </div>
            `
        },
        'manual': {
            title: 'Manual Trigger',
            category: 'trigger',
            icon: 'fas fa-hand-pointer',
            html: `
                <div class="node node-trigger" data-node-id="${nodeId}" style="left: ${x}px; top: ${y}px;">
                    <div class="node-header">
                        <span><i class="fas fa-hand-pointer"></i> Manual</span>
                        <i class="fas fa-grip-vertical"></i>
                    </div>
                    <div class="node-content">
                        <p class="text-sm">Run this workflow manually</p>
                        <div class="node-io">
                            <div class
