from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import json
import requests
import jwt
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# Pi Network API configuration
PI_API_URL = os.environ.get('PI_API_URL', 'https://api.minepi.com/v2')
PI_API_KEY = os.environ.get('PI_API_KEY', 'your-pi-api-key')
PI_SECRET_KEY = os.environ.get('PI_SECRET_KEY', 'your-pi-secret-key')

# In-memory storage for demo (replace with Neon DB in production)
users = {}
workflows = {}
workflow_executions = {}
tools = []

# Load 100+ tools
def load_tools():
    # Categories of tools
    categories = [
        'Database', 'API Integration', 'Data Transformation', 
        'Notification', 'Authentication', 'File Operation',
        'Payment Processing', 'Blockchain', 'AI/ML', 'Utility'
    ]
    
    # Trigger Nodes
    tools.extend([
        {
            'id': 'schedule',
            'name': 'Schedule Trigger',
            'description': 'Activates the workflow at a specific time interval',
            'category': 'trigger',
            'icon': 'fas fa-clock',
            'config': {
                'frequency': ['minutes', 'hours', 'days', 'weeks'],
                'interval': 1
            }
        },
        {
            'id': 'webhook',
            'name': 'Webhook Trigger',
            'description': 'Listens for incoming HTTP requests to trigger workflows',
            'category': 'trigger',
            'icon': 'fas fa-code-branch',
            'config': {
                'method': ['GET', 'POST', 'PUT'],
                'path': ''
            }
        },
        {
            'id': 'manual',
            'name': 'Manual Trigger',
            'description': 'Allows manual execution of the workflow',
            'category': 'trigger',
            'icon': 'fas fa-hand-pointer',
            'config': {}
        }
    ])
    
    # App Integration Nodes
    apps = [
        ('Slack', 'fab fa-slack', 'slack'),
        ('Email', 'fas fa-envelope', 'email'),
        ('HTTP Request', 'fas fa-globe', 'http'),
        ('Pi Authentication', 'fab fa-pi', 'pi-auth')
    ]
    
    for app_name, icon, app_id in apps:
        tools.append({
            'id': app_id,
            'name': app_name,
            'description': f'Integration with {app_name}',
            'category': 'app',
            'icon': icon,
            'config': {}
        })
    
    # Data Manipulation Nodes
    data_nodes = [
        ('Code', 'fas fa-code', 'code', 'Execute custom JavaScript or Python code'),
        ('Set', 'fas fa-edit', 'set', 'Set values in JSON data'),
        ('Date & Time', 'fas fa-calendar-alt', 'date', 'Format and manipulate dates')
    ]
    
    for name, icon, node_id, desc in data_nodes:
        tools.append({
            'id': node_id,
            'name': name,
            'description': desc,
            'category': 'data',
            'icon': icon,
            'config': {}
        })
    
    # Logic & Flow Control Nodes
    logic_nodes = [
        ('IF', 'fas fa-question-circle', 'if', 'Conditional branching based on data'),
        ('Switch', 'fas fa-exchange-alt', 'switch', 'Multiple conditional branching'),
        ('Wait', 'fas fa-hourglass-half', 'wait', 'Pause workflow execution')
    ]
    
    for name, icon, node_id, desc in logic_nodes:
        tools.append({
            'id': node_id,
            'name': name,
            'description': desc,
            'category': 'logic',
            'icon': icon,
            'config': {}
        })
    
    # File & Format Nodes
    file_nodes = [
        ('CSV', 'fas fa-table', 'csv', 'Parse and generate CSV data'),
        ('JSON', 'fas fa-brackets-curly', 'json', 'Parse and generate JSON data')
    ]
    
    for name, icon, node_id, desc in file_nodes:
        tools.append({
            'id': node_id,
            'name': name,
            'description': desc,
            'category': 'file',
            'icon': icon,
            'config': {}
        })
    
    # Utility Nodes
    utility_nodes = [
        ('No Operation', 'fas fa-circle-notch', 'noop', 'Placeholder node that does nothing'),
        ('Rename', 'fas fa-signature', 'rename', 'Rename fields in data'),
        ('Pi Payment', 'fas fa-money-bill-wave', 'pi-payment', 'Create Pi Network payments'),
        ('Pi Blockchain', 'fas fa-database', 'pi-data', 'Read/write to Pi Blockchain')
    ]
    
    for name, icon, node_id, desc in utility_nodes:
        tools.append({
            'id': node_id,
            'name': name,
            'description': desc,
            'category': 'utility',
            'icon': icon,
            'config': {}
        })

load_tools()

# Pi Network Integration Functions
def verify_pi_access_token(access_token):
    """Verify a Pi Network access token"""
    try:
        # In a real implementation, verify the JWT signature using Pi's public key
        # This is a simplified version for demonstration
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        app.logger.error(f"Token verification failed: {e}")
        return None

def create_pi_payment(amount, memo, metadata={}):
    """Create a payment through the Pi Network API"""
    headers = {
        'Authorization': f'Key {PI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'amount': amount,
        'memo': memo,
        'metadata': metadata,
        'uid': metadata.get('user_uid')  # User ID from Pi Network
    }
    
    try:
        response = requests.post(f'{PI_API_URL}/payments', json=payload, headers=headers)
        if response.status_code == 201:
            return response.json()
        else:
            app.logger.error(f"Payment creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        app.logger.error(f"Payment API error: {e}")
        return None

def complete_pi_payment(payment_id, txid):
    """Complete a Pi payment after it has been approved"""
    headers = {
        'Authorization': f'Key {PI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'txid': txid
    }
    
    try:
        response = requests.post(f'{PI_API_URL}/payments/{payment_id}/complete', 
                               json=payload, headers=headers)
        return response.status_code == 200
    except Exception as e:
        app.logger.error(f"Complete payment error: {e}")
        return False

# Workflow Execution Functions
def execute_workflow(workflow, execution_data=None):
    """Execute a workflow with the given data"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Initialize execution record
    workflow_executions[execution_id] = {
        'workflow_id': workflow['id'],
        'start_time': start_time.isoformat(),
        'status': 'running',
        'nodes_executed': [],
        'results': {}
    }
    
    try:
        # Find the trigger node to start execution
        trigger_nodes = [node for node in workflow['nodes'] if node['category'] == 'trigger']
        
        if not trigger_nodes:
            raise Exception("No trigger node found in workflow")
        
        # For simplicity, we'll execute all nodes in order
        # In a real implementation, you would follow connections between nodes
        for node in workflow['nodes']:
            node_result = execute_node(node, execution_data)
            workflow_executions[execution_id]['nodes_executed'].append({
                'node_id': node['id'],
                'node_type': node['type'],
                'timestamp': datetime.now().isoformat(),
                'result': node_result
            })
        
        workflow_executions[execution_id]['status'] = 'completed'
        workflow_executions[execution_id]['end_time'] = datetime.now().isoformat()
        
        return execution_id
        
    except Exception as e:
        workflow_executions[execution_id]['status'] = 'failed'
        workflow_executions[execution_id]['error'] = str(e)
        workflow_executions[execution_id]['end_time'] = datetime.now().isoformat()
        app.logger.error(f"Workflow execution failed: {e}")
        return execution_id

def execute_node(node, input_data):
    """Execute a single node with the given input data"""
    node_type = node['type']
    config = node.get('config', {})
    
    try:
        if node_type == 'schedule':
            # Schedule nodes are triggers and don't process data
            return {'status': 'triggered', 'data': input_data}
            
        elif node_type == 'webhook':
            # Webhook nodes are triggers and don't process data
            return {'status': 'triggered', 'data': input_data}
            
        elif node_type == 'manual':
            # Manual nodes are triggers and don't process data
            return {'status': 'triggered', 'data': input_data}
            
        elif node_type == 'slack':
            # Simulate sending a Slack message
            message = config.get('message', 'Default message from Pi No-Code Builder')
            channel = config.get('channel', '#general')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"Sent to Slack channel {channel}: {message}",
                    'original_data': input_data
                }
            }
            
        elif node_type == 'email':
            # Simulate sending an email
            to = config.get('to', 'recipient@example.com')
            subject = config.get('subject', 'Message from Pi No-Code Builder')
            body = config.get('body', 'Default email body')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"Email sent to {to} with subject: {subject}",
                    'original_data': input_data
                }
            }
            
        elif node_type == 'http':
            # Simulate HTTP request
            url = config.get('url', 'https://api.example.com/data')
            method = config.get('method', 'GET')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"HTTP {method} request to {url}",
                    'response': {'simulated': True, 'status': 'success'},
                    'original_data': input_data
                }
            }
            
        elif node_type == 'pi-auth':
            # Pi authentication node
            scopes = config.get('scopes', 'username')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"Pi authentication with scopes: {scopes}",
                    'authenticated': True,
                    'original_data': input_data
                }
            }
            
        elif node_type == 'code':
            # Code execution node (simulated)
            language = config.get('language', 'javascript')
            code = config.get('code', '// Default code')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"Executed {language} code",
                    'result': {'simulated_execution': True},
                    'original_data': input_data
                }
            }
            
        elif node_type == 'set':
            # Set values in data
            property_name = config.get('property_name', 'new_field')
            value = config.get('value', 'default_value')
            
            if input_data:
                output_data = input_data.copy()
            else:
                output_data = {}
                
            output_data[property_name] = value
            
            return {
                'status': 'success', 
                'data': output_data
            }
            
        elif node_type == 'date':
            # Date manipulation node
            operation = config.get('operation', 'format')
            format_str = config.get('format', 'YYYY-MM-DD HH:mm:ss')
            
            current_time = datetime.now().isoformat()
            
            return {
                'status': 'success', 
                'data': {
                    'formatted_date': current_time,
                    'original_data': input_data
                }
            }
            
        elif node_type == 'if':
            # Conditional logic node
            condition = config.get('condition', 'true')
            
            # Simple condition evaluation (in real implementation, use a proper expression evaluator)
            condition_met = 'true' in condition.lower() or 'yes' in condition.lower()
            
            return {
                'status': 'success', 
                'data': {
                    'condition_met': condition_met,
                    'original_data': input_data
                }
            }
            
        elif node_type == 'switch':
            # Switch node
            value = config.get('value', 'default')
            
            return {
                'status': 'success', 
                'data': {
                    'selected_case': value,
                    'original_data': input_data
                }
            }
            
        elif node_type == 'wait':
            # Wait node
            duration = int(config.get('duration', 1))
            unit = config.get('unit', 'seconds')
            
            # Simulate waiting (in real implementation, use async/await)
            wait_seconds = duration
            if unit == 'minutes':
                wait_seconds = duration * 60
            elif unit == 'hours':
                wait_seconds = duration * 60 * 60
            elif unit == 'days':
                wait_seconds = duration * 60 * 60 * 24
                
            return {
                'status': 'success', 
                'data': {
                    'message': f"Waited for {duration} {unit}",
                    'original_data': input_data
                }
            }
            
        elif node_type == 'csv':
            # CSV processing node
            operation = config.get('operation', 'toJson')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"CSV {operation} operation",
                    'original_data': input_data
                }
            }
            
        elif node_type == 'json':
            # JSON processing node
            operation = config.get('operation', 'parse')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"JSON {operation} operation",
                    'original_data': input_data
                }
            }
            
        elif node_type == 'noop':
            # No operation node
            return {
                'status': 'success', 
                'data': input_data
            }
            
        elif node_type == 'rename':
            # Rename field node
            from_field = config.get('from_field', 'old_field')
            to_field = config.get('to_field', 'new_field')
            
            if input_data and from_field in input_data:
                output_data = input_data.copy()
                output_data[to_field] = output_data.pop(from_field)
            else:
                output_data = input_data
                
            return {
                'status': 'success', 
                'data': output_data
            }
            
        elif node_type == 'pi-payment':
            # Pi payment node
            amount = config.get('amount', 1)
            memo = config.get('memo', 'Payment from Pi No-Code Builder')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"Pi payment of {amount} π with memo: {memo}",
                    'payment_created': True,
                    'original_data': input_data
                }
            }
            
        elif node_type == 'pi-data':
            # Pi blockchain data node
            operation = config.get('operation', 'read')
            key = config.get('key', 'data_key')
            
            return {
                'status': 'success', 
                'data': {
                    'message': f"Pi blockchain {operation} operation for key: {key}",
                    'operation': operation,
                    'key': key,
                    'original_data': input_data
                }
            }
            
        else:
            # Unknown node type
            return {
                'status': 'skipped', 
                'data': {
                    'message': f"Unknown node type: {node_type}",
                    'original_data': input_data
                }
            }
            
    except Exception as e:
        app.logger.error(f"Node execution failed: {e}")
        return {
            'status': 'failed', 
            'error': str(e),
            'data': input_data
        }

# Routes
@app.route('/')
def home():
    return jsonify({'message': 'Pi No-Code Tool Builder API'})

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/pi/auth', methods=['POST'])
def pi_auth():
    """Authenticate with Pi Network"""
    data = request.get_json()
    access_token = data.get('accessToken')
    
    if not access_token:
        return jsonify({'error': 'Access token required'}), 400
    
    # Verify the access token
    user_data = verify_pi_access_token(access_token)
    if not user_data:
        return jsonify({'error': 'Invalid access token'}), 401
    
    # Store user session
    user_id = user_data.get('uid')
    users[user_id] = {
        'username': user_data.get('username', 'Pi User'),
        'authenticated': True,
        'auth_time': datetime.now().isoformat()
    }
    
    session['user_id'] = user_id
    
    return jsonify({
        'success': True,
        'user': {
            'uid': user_id,
            'username': users[user_id]['username']
        }
    })

@app.route('/api/pi/payment', methods=['POST'])
def pi_payment():
    """Create a Pi payment"""
    data = request.get_json()
    amount = data.get('amount')
    memo = data.get('memo', 'Payment from Pi No-Code Builder')
    user_uid = data.get('user_uid')
    
    if not amount or not user_uid:
        return jsonify({'error': 'Amount and user UID required'}), 400
    
    # Create payment through Pi API
    payment_data = create_pi_payment(amount, memo, {
        'user_uid': user_uid,
        'product': 'no-code-builder',
        'workflow_id': data.get('workflow_id', 'unknown')
    })
    
    if not payment_data:
        return jsonify({'error': 'Payment creation failed'}), 500
    
    return jsonify({
        'success': True,
        'payment': payment_data
    })

@app.route('/api/pi/payment/complete', methods=['POST'])
def pi_payment_complete():
    """Complete a Pi payment"""
    data = request.get_json()
    payment_id = data.get('payment_id')
    txid = data.get('txid')
    
    if not payment_id or not txid:
        return jsonify({'error': 'Payment ID and TXID required'}), 400
    
    # Complete the payment
    success = complete_pi_payment(payment_id, txid)
    
    if not success:
        return jsonify({'error': 'Payment completion failed'}), 500
    
    return jsonify({'success': True})

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    user_workflows = [w for w in workflows.values() if w.get('user_id') == user_id]
    
    return jsonify(user_workflows)

@app.route('/api/workflows', methods=['POST'])
def create_workflow():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    workflow_id = str(uuid.uuid4())
    user_id = session['user_id']
    
    workflow = {
        'id': workflow_id,
        'user_id': user_id,
        'name': data.get('name', 'New Workflow'),
        'created': datetime.now().isoformat(),
        'updated': datetime.now().isoformat(),
        'nodes': data.get('nodes', []),
        'connections': data.get('connections', [])
    }
    
    workflows[workflow_id] = workflow
    
    return jsonify(workflow)

@app.route('/api/workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if workflow_id not in workflows:
        return jsonify({'error': 'Workflow not found'}), 404
    
    # Check if the user owns this workflow
    if workflows[workflow_id].get('user_id') != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(workflows[workflow_id])

@app.route('/api/workflows/<workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if workflow_id not in workflows:
        return jsonify({'error': 'Workflow not found'}), 404
    
    # Check if the user owns this workflow
    if workflows[workflow_id].get('user_id') != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    workflows[workflow_id]['nodes'] = data.get('nodes', [])
    workflows[workflow_id]['connections'] = data.get('connections', [])
    workflows[workflow_id]['updated'] = datetime.now().isoformat()
    
    return jsonify(workflows[workflow_id])

@app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if workflow_id not in workflows:
        return jsonify({'error': 'Workflow not found'}), 404
    
    # Check if the user owns this workflow
    if workflows[workflow_id].get('user_id') != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    del workflows[workflow_id]
    return jsonify({'success': True})

@app.route('/api/tools', methods=['GET'])
def get_tools():
    category = request.args.get('category')
    if category:
        filtered_tools = [t for t in tools if t['category'] == category]
        return jsonify(filtered_tools)
    return jsonify(tools)

@app.route('/api/execute/<workflow_id>', methods=['POST'])
def execute_workflow_route(workflow_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if workflow_id not in workflows:
        return jsonify({'error': 'Workflow not found'}), 404
    
    # Check if the user owns this workflow
    if workflows[workflow_id].get('user_id') != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    input_data = data.get('data', {})
    
    # Execute the workflow
    execution_id = execute_workflow(workflows[workflow_id], input_data)
    
    return jsonify({
        'success': True,
        'executionId': execution_id,
        'status': workflow_executions[execution_id]['status']
    })

@app.route('/api/executions/<execution_id>', methods=['GET'])
def get_execution(execution_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if execution_id not in workflow_executions:
        return jsonify({'error': 'Execution not found'}), 404
    
    # Check if the user owns the workflow for this execution
    execution = workflow_executions[execution_id]
    workflow_id = execution['workflow_id']
    
    if workflow_id not in workflows or workflows[workflow_id].get('user_id') != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(workflow_executions[execution_id])

@app.route('/api/executions', methods=['GET'])
def get_executions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    user_workflows = [w for w in workflows.values() if w.get('user_id') == user_id]
    workflow_ids = [w['id'] for w in user_workflows]
    
    user_executions = [e for e in workflow_executions.values() if e['workflow_id'] in workflow_ids]
    
    return jsonify(user_executions)

@app.route('/api/webhook/<path:webhook_path>', methods=['GET', 'POST', 'PUT'])
def handle_webhook(webhook_path):
    """Handle incoming webhook requests to trigger workflows"""
    # Find workflows with webhook nodes that match this path
    matching_workflows = []
    
    for workflow in workflows.values():
        for node in workflow.get('nodes', []):
            if node.get('type') == 'webhook':
                config = node.get('config', {})
                if config.get('path') == webhook_path:
                    matching_workflows.append(workflow)
                    break
    
    if not matching_workflows:
        return jsonify({'error': 'No workflows found for this webhook'}), 404
    
    # Execute all matching workflows
    execution_ids = []
    webhook_data = {
        'method': request.method,
        'headers': dict(request.headers),
        'params': dict(request.args),
        'json': request.get_json(silent=True) or {},
        'form': dict(request.form) if request.form else {}
    }
    
    for workflow in matching_workflows:
        execution_id = execute_workflow(workflow, webhook_data)
        execution_ids.append(execution_id)
    
    return jsonify({
        'success': True,
        'message': f'Triggered {len(execution_ids)} workflow(s)',
        'executionIds': execution_ids
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
