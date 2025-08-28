    // Initialize Pi SDK
    const Pi = window.Pi;
    let piSDK = null;

    // Store workflow data
    let workflowNodes = [];
    let workflowConnections = [];
    let currentNodeId = 1;
    let selectedNode = null;
    let offsetX = 0, offsetY = 0;

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

        // Initialize node dragging
        initNodeDragging();
    });

    // Simple login functionality
    document.querySelector('.login-btn').addEventListener('click', function() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if (email && password) {
            document.getElementById('loginScreen').style.display = 'none';
            document.getElementById('appContainer').style.display = 'flex';
        } else {
            alert('Please enter both email and password');
        }
    });

    // Pi Network login
    document.getElementById('piLoginBtn').addEventListener('click', function() {
        authenticateWithPi();
    });

    // Connect Pi button
    document.getElementById('connectPiBtn').addEventListener('click', function() {
        document.getElementById('piConnectModal').style.display = 'flex';
    });

    // Close modal
    document.querySelector('.close-modal').addEventListener('click', function() {
        document.getElementById('piConnectModal').style.display = 'none';
    });

    // Modal option clicks
    document.getElementById('piAuthOption').addEventListener('click', function() {
        addNodeToCanvas('pi-auth');
        document.getElementById('piConnectModal').style.display = 'none';
    });

    document.getElementById('piPaymentOption').addEventListener('click', function() {
        addNodeToCanvas('pi-payment');
        document.getElementById('piConnectModal').style.display = 'none';
    });

    document.getElementById('piDataOption').addEventListener('click', function() {
        addNodeToCanvas('pi-data');
        document.getElementById('piConnectModal').style.display = 'none';
    });

    // New Workflow button functionality
    document.getElementById('newWorkflowBtn').addEventListener('click', function() {
        document.getElementById('dashboardView').style.display = 'none';
        document.getElementById('editorView').style.display = 'flex';
    });

    // Execute Workflow button
    document.getElementById('executeWorkflowBtn').addEventListener('click', function() {
        executeWorkflow();
    });

    // Initialize node dragging from palette
    function initNodeDragging() {
        const nodeItems = document.querySelectorAll('.node-item');
        
        nodeItems.forEach(item => {
            item.addEventListener('dragstart', function(e) {
                const nodeType = this.getAttribute('data-type');
                e.dataTransfer.setData('nodeType', nodeType);
            });
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
    }

    // Make nodes draggable
    function makeNodeDraggable(node) {
        const header = node.querySelector('.node-header');
        
        header.addEventListener('mousedown', function(e) {
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
                
                // Update node position in data model
                const nodeId = node.getAttribute('data-node-id');
                const nodeIndex = workflowNodes.findIndex(n => n.id === nodeId);
                if (nodeIndex !== -1) {
                    workflowNodes[nodeIndex].x = parseInt(node.style.left || '0');
                    workflowNodes[nodeIndex].y = parseInt(node.style.top || '0');
                }
            }
            
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
        
        // Prevent text selection while dragging
        header.addEventListener('selectstart', function(e) {
            e.preventDefault();
            return false;
        });
    }

    // Update connections when node moves (placeholder for connection functionality)
    function updateNodeConnections(node) {
        // This would update any connection lines if you implement them
        console.log('Node moved, would update connections here');
    }

    // Add a node to the canvas
    function addNodeToCanvas(nodeType, x = 100, y = 100) {
        const canvas = document.getElementById('workflowCanvas');
        const nodeId = 'node-' + currentNodeId++;
        
        let nodeHtml = '';
        let nodeTitle = '';
        let nodeCategory = '';
        
        switch(nodeType) {
            case 'schedule':
                nodeTitle = 'Schedule Trigger';
                nodeCategory = 'trigger';
                nodeHtml = `
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
                `;
                break;
                
            case 'webhook':
                nodeTitle = 'Webhook Trigger';
                nodeCategory = 'trigger';
                nodeHtml = `
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
                `;
                break;
                
            // Add other node cases here (truncated for brevity)
            // ... [Include all the other node cases from your original code]
            
            case 'pi-payment':
                nodeTitle = 'Pi Payment';
                nodeCategory = 'utility';
                nodeHtml = `
                    <div class="node node-pi" data-node-id="${nodeId}" style="left: ${x}px; top: ${y}px;">
                        <div class="node-header">
                            <span><i class="fas fa-money-bill-wave"></i> Pi Payment</span>
                            <i class="fas fa-grip-vertical"></i>
                        </div>
                        <div class="node-content">
                            <div class="form-group">
                                <label>Amount (π)</label>
                                <input type="number" value="1" min="0.1" step="0.1">
                            </div>
                            <div class="form-group">
                                <label>Memo</label>
                                <input type="text" placeholder="Payment for services">
                            </div>
                            <div class="node-io">
                                <div class="input-point"></div>
                                <div class="output-point"></div>
                            </div>
                        </div>
                    </div>
                `;
                break;
                
            case 'pi-data':
                nodeTitle = 'Pi Blockchain Data';
                nodeCategory = 'utility';
                nodeHtml = `
                    <div class="node node-pi" data-node-id="${nodeId}" style="left: ${x}px; top: ${y}px;">
                        <div class="node-header">
                            <span><i class="fas fa-database"></i> Pi Blockchain</span>
                            <i class="fas fa-grip-vertical"></i>
                        </div>
                        <div class="node-content">
                            <div class="form-group">
                                <label>Operation</label>
                                <select>
                                    <option value="read">Read Data</option>
                                    <option value="write">Write Data</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Key</label>
                                <input type="text" placeholder="data_key">
                            </div>
                            <div class="node-io">
                                <div class="input-point"></div>
                                <div class="output-point"></div>
                            </div>
                        </div>
                    </div>
                `;
                break;
        }
        
        // Add node to canvas
        canvas.insertAdjacentHTML('beforeend', nodeHtml);
        
        // Make new node draggable
        const newNode = document.querySelector(`[data-node-id="${nodeId}"]`);
        makeNodeDraggable(newNode);
        
        // Add to workflow data model
        workflowNodes.push({
            id: nodeId,
            type: nodeType,
            category: nodeCategory,
            title: nodeTitle,
            x: x,
            y: y,
            config: {}
        });
    }

    // Execute the workflow
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
        alert(`Executing workflow with ${workflowNodes.length} nodes starting with ${startNodes[0].title}`);
        
        // In a real implementation, this would send the workflow to the backend for execution
        // For now, we'll just simulate execution
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

    // Pi Network Authentication Function
    function authenticateWithPi() {
        if (!piSDK) {
            alert('Pi SDK not initialized. Please try again.');
            return;
        }

        // Define the scopes you need
        const scopes = ['username', 'payments', 'wallet_address'];
        
        // Authenticate the user
        piSDK.auth
        .then(authResult => {
            console.log('Pi authentication successful', authResult);
            
            // Store the session
            const sessionData = {
                authenticated: true,
                expires: Date.now() + (7 * 24 * 60 * 60 * 1000), // 7 days from now
                user: {
                    uid: authResult.user.uid,
                    username: authResult.user.username,
                    accessToken: authResult.accessToken
                }
            };
            
            localStorage.setItem('piUserSession', JSON.stringify(sessionData));
            
            // Update UI and show main app
            document.getElementById('loginScreen').style.display = 'none';
            document.getElementById('appContainer').style.display = 'flex';
            updateUIWithUserData(sessionData.user);
        })
        .catch(error => {
            console.error('Pi authentication failed', error);
            alert('Authentication with Pi Network failed. Please try again.');
        });
    }

    function updateUIWithUserData(user) {
        // Update user section in sidebar
        const userAvatar = document.querySelector('.user-avatar');
        const userName = document.querySelector('.user-name');
        
        userAvatar.textContent = user.username ? user.username.charAt(0).toUpperCase() : 'P';
        userName.textContent = user.username || 'Pi User';
        
        // Add Pi badge to user role
        const userRole = document.querySelector('.user-role');
        userRole.innerHTML = 'Pro Plan <span class="badge badge-pi">Pi Verified</span>';
    }

    // Example function to create a Pi payment
    function createPiPayment(amount, memo, callback) {
        if (!piSDK) {
            console.error('Pi SDK not initialized');
            return;
        }
        
        const paymentData = {
            amount: amount,
            memo: memo,
            metadata: { 
                workflowId: 'current-workflow-id' 
            }
        };
        
        piSDK.createPayment(paymentData)
            .then(payment => {
                console.log('Payment created', payment);
                if (callback) callback(null, payment);
            })
            .catch(error => {
                console.error('Payment error', error);
                if (callback) callback(error, null);
            });
    }

    // Example function to authenticate with Pi
    function piAuthenticate(scopes, callback) {
        if (!piSDK) {
            console.error('Pi SDK not initialized');
            return;
        }
        
        piSDK.authenticate(scopes)
            .then(authResult => {
                console.log('Authentication successful', authResult);
                if (callback) callback(null, authResult);
            })
            .catch(error => {
                console.error('Authentication error', error);
                if (callback) callback(error, null);
            });
    }
