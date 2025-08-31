from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import json
import requests
import jwt
import os
import logging
from logging.handlers import RotatingFileHandler
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__, static_folder='.', static_url_path='')
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

# Database configuration
def get_db_connection():
    """Create and return a database connection"""
    try:
        # For Neon DB or PostgreSQL
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            database=os.environ.get('DB_NAME', 'pi_nocode_builder'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'password'),
            port=os.environ.get('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        app.logger.error(f"Database connection failed: {e}")
        return None

# Initialize database tables
def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        app.logger.error("Failed to initialize database")
        return False
    
    try:
        with conn.cursor() as cur:
            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    pi_uid VARCHAR(255),
                    pi_username VARCHAR(255),
                    pi_access_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Workflows table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id VARCHAR(255) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    nodes JSONB,
                    connections JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'draft'
                )
            """)
            
            # Workflow executions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id VARCHAR(255) PRIMARY KEY,
                    workflow_id VARCHAR(255) REFERENCES workflows(id),
                    status VARCHAR(50) NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    results JSONB,
                    error_message TEXT
                )
            """)
            
            # API keys table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    key VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            """)
            
            conn.commit()
            app.logger.info("Database initialized successfully")
            return True
            
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Initialize database on startup
init_db()

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

# Authentication middleware
def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify session is still valid
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE id = %s", (session['user_id'],))
                user = cur.fetchone()
                
                if not user:
                    session.clear()
                    return jsonify({'error': 'User not found'}), 401
        except Exception as e:
            app.logger.error(f"Auth verification failed: {e}")
            return jsonify({'error': 'Authentication verification failed'}), 500
        finally:
            conn.close()
            
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def serve_index():
    """Serve the main application"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if get_db_connection() else 'disconnected'
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'),\ 500
        
    try:
        with conn.cursor() as cur:
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({'error': 'User already exists'}), 409
            
            # Create new user
            password_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, password_hash)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            
            # Create session
            session['user_id'] = user_id
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user': {'id': user_id, 'email': email}
            })
            
    except Exception as e:
        app.logger.error(f"Registration failed: {e}")
        conn.rollback()
        return jsonify({'error': 'Registration failed'}), 500
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login with email and password"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find user
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            
            if not user or not check_password_hash(user['password_hash'], password):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Update last login
            cur.execute(
                "UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.now(), user['id'])
            )
            conn.commit()
            
            # Create session
            session['user_id'] = user['id']
            session.permanent = True
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'pi_username': user['pi_username']
                }
            })
            
    except Exception as e:
        app.logger.error(f"Login failed: {e}")
        return jsonify({'error': 'Login failed'}), 500
    finally:
        conn.close()

@app.route('/api/auth/pi', methods=['POST'])
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
    
    # Get or create user
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if user already exists with this Pi UID
            cur.execute("SELECT * FROM users WHERE pi_uid = %s", (user_data.get('uid'),))
            user = cur.fetchone()
            
            if not user:
                # Create new user with Pi authentication
                cur.execute(
                    """INSERT INTO users (pi_uid, pi_username, pi_access_token, last_login) 
                    VALUES (%s, %s, %s, %s) RETURNING *""",
                    (user_data.get('uid'), user_data.get('username'), access_token, datetime.now())
                )
                user = cur.fetchone()
            else:
                # Update existing user
                cur.execute(
                    """UPDATE users SET pi_username = %s, pi_access_token = %s, last_login = %s 
                    WHERE id = %s RETURNING *""",
                    (user_data.get('username'), access_token, datetime.now(), user['id'])
                )
                user = cur.fetchone()
            
            conn.commit()
            
            # Create session
            session['user_id'] = user['id']
            session.permanent = True
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'pi_uid': user['pi_uid'],
                    'pi_username': user['pi_username']
                }
            })
            
    except Exception as e:
        app.logger.error(f"Pi authentication failed: {e}")
        conn.rollback()
        return jsonify({'error': 'Pi authentication failed'}), 500
    finally:
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout the current user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/status')
def auth_status():
    """Check authentication status"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'authenticated': False})
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, email, pi_uid, pi_username FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()
            
            if user:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'pi_uid': user['pi_uid'],
                        'pi_username': user['pi_username']
                    }
                })
            else:
                session.clear()
                return jsonify({'authenticated': False})
                
    except Exception as e:
        app.logger.error(f"Auth status check failed: {e}")
        return jsonify({'authenticated': False})
    finally:
        conn.close()

@app.route('/api/pi/payment', methods=['POST'])
@require_auth
def pi_payment():
    """Create a Pi payment"""
    data = request.get_json()
    amount = data.get('amount')
    memo = data.get('memo', 'Payment from Pi No-Code Builder')
    
    if not amount:
        return jsonify({'error': 'Amount required'}), 400
    
    # Get user's Pi UID
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT pi_uid, pi_access_token FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()
            
            if not user or not user['pi_uid']:
                return jsonify({'error': 'Pi account not linked'}), 400
            
            # Create payment through Pi API
            payment_data = create_pi_payment(amount, memo, {
                'user_uid': user['pi_uid'],
                'user_id': session['user_id'],
                'product': 'no-code-builder'
            })
            
            if not payment_data:
                return jsonify({'error': 'Payment creation failed'}), 500
            
            return jsonify({
                'success': True,
                'payment': payment_data
            })
            
    except Exception as e:
        app.logger.error(f"Payment creation failed: {e}")
        return jsonify({'error': 'Payment creation failed'}), 500
    finally:
        conn.close()

@app.route('/api/pi/payment/complete', methods=['POST'])
@require_auth
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
@require_auth
def get_workflows():
    """Get all workflows for the current user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, description, status, created_at, updated_at FROM workflows WHERE user_id = %s ORDER BY updated_at DESC",
                (session['user_id'],)
            )
            workflows = cur.fetchall()
            
            return jsonify([dict(w) for w in workflows])
            
    except Exception as e:
        app.logger.error(f"Failed to get workflows: {e}")
        return jsonify({'error': 'Failed to get workflows'}), 500
    finally:
        conn.close()

@app.route('/api/workflows', methods=['POST'])
@require_auth
def create_workflow():
    """Create a new workflow"""
    data = request.get_json()
    name = data.get('name', 'New Workflow')
    description = data.get('description', '')
    
    workflow_id = f"wf-{uuid.uuid4().hex}"
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO workflows (id, user_id, name, description, nodes, connections) 
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (workflow_id, session['user_id'], name, description, json.dumps([]), json.dumps([]))
            )
            conn.commit()
            
            return jsonify({
                'id': workflow_id,
                'name': name,
                'description': description,
                'nodes': [],
                'connections': [],
                'status': 'draft',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
            
    except Exception as e:
        app.logger.error(f"Failed to create workflow: {e}")
        conn.rollback()
        return jsonify({'error': 'Failed to create workflow'}), 500
    finally:
        conn.close()

@app.route('/api/workflows/<workflow_id>', methods=['GET'])
@require_auth
def get_workflow(workflow_id):
    """Get a specific workflow"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM workflows WHERE id = %s AND user_id = %s",
                (workflow_id, session['user_id'])
            )
            workflow = cur.fetchone()
            
            if not workflow:
                return jsonify({'error': 'Workflow not found'}), 404
            
            return jsonify(dict(workflow))
            
    except Exception as e:
        app.logger.error(f"Failed to get workflow: {e}")
        return jsonify({'error': 'Failed to get workflow'}), 500
    finally:
        conn.close()

@app.route('/api/workflows/<workflow_id>', methods=['PUT'])
@require_auth
def update_workflow(workflow_id):
    """Update a workflow"""
    data = request.get_json()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify the user owns this workflow
            cur.execute(
                "SELECT id FROM workflows WHERE id = %s AND user_id = %s",
                (workflow_id, session['user_id'])
            )
            if not cur.fetchone():
                return jsonify({'error': 'Workflow not found'),\ 404
            
            # Build update query based on provided fields
            update_fields = []
            update_values = []
            
            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])
            
            if 'description' in data:
                update_fields.append("description = %s")
                update_values.append(data['description'])
            
            if 'nodes' in data:
                update_fields.append("nodes = %s")
                update_values.append(json.dumps(data['nodes']))
            
            if 'connections' in data:
                update_fields.append("connections = %s")
                update_values.append(json.dumps(data['connections']))
            
            if 'status' in data:
                update_fields.append("status = %s")
                update_values.append(data['status'])
            
            # Always update the updated_at field
            update_fields.append("updated_at = %s")
            update_values.append(datetime.now())
            
            # Execute update
            update_values.append(workflow_id)
            update_values.append(session['user_id'])
            
            cur.execute(
                f"UPDATE workflows SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s RETURNING *",
                update_values
            )
            
            workflow = cur.fetchone()
            conn.commit()
            
            return jsonify(dict(workflow))
            
    except Exception as e:
        app.logger.error(f"Failed to update workflow: {e}")
        conn.rollback()
        return jsonify({'error': 'Failed to update workflow'}), 500
    finally:
        conn.close()

@app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
@require_auth
def delete_workflow(workflow_id):
    """Delete a workflow"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor() as cur:
            # Verify the user owns this workflow
            cur.execute(
                "SELECT id FROM workflows WHERE id = %s AND user_id = %s",
                (workflow_id, session['user_id'])
            )
            if not cur.fetchone():
                return jsonify({'error': 'Workflow not found'}), 404
            
            # Delete the workflow
            cur.execute(
                "DELETE FROM workflows WHERE id = %s AND user_id = %s",
                (workflow_id, session['user_id'])
            )
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Workflow deleted successfully'})
            
    except Exception as e:
        app.logger.error(f"Failed to delete workflow: {e}")
        conn.rollback()
        return jsonify({'error': 'Failed to delete workflow'}), 500
    finally:
        conn.close()

@app.route('/api/workflows/<workflow_id>/execute', methods=['POST'])
@require_auth
def execute_workflow(workflow_id):
    """Execute a workflow"""
    data = request.get_json()
    input_data = data.get('data', {})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the workflow
            cur.execute(
                "SELECT * FROM workflows WHERE id = %s AND user_id = %s",
                (workflow_id, session['user_id'])
            )
            workflow = cur.fetchone()
            
            if not workflow:
                return jsonify({'error': 'Workflow not found'}), 404
            
            # Create execution record
            execution_id = f"exec-{uuid.uuid4().hex}"
            cur.execute(
                """INSERT INTO workflow_executions (id, workflow_id, status, started_at) 
                VALUES (%s, %s, %s, %s)""",
                (execution_id, workflow_id, 'running', datetime.now())
            )
            conn.commit()
            
            # In a real implementation, this would execute the workflow
            # For now, we'll simulate execution and return immediately
            
            # Simulate execution completion after a short delay
            # In a real implementation, this would be handled asynchronously
            
            return jsonify({
                'success': True,
                'executionId': execution_id,
                'status': 'started',
                'message': 'Workflow execution started'
            })
            
    except Exception as e:
        app.logger.error(f"Failed to execute workflow: {e}")
        return jsonify({'error': 'Failed to execute workflow'}), 500
    finally:
        conn.close()

@app.route('/api/executions/<execution_id>', methods=['GET'])
@require_auth
def get_execution(execution_id):
    """Get execution details"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the execution
            cur.execute("""
                SELECT e.*, w.name as workflow_name 
                FROM workflow_executions e
                JOIN workflows w ON e.workflow_id = w.id
                WHERE e.id = %s AND w.user_id = %s
            """, (execution_id, session['user_id']))
            
            execution = cur.fetchone()
            
            if not execution:
                return jsonify({'error': 'Execution not found'}), 404
            
            return jsonify(dict(execution))
            
    except Exception as e:
        app.logger.error(f"Failed to get execution: {e}")
        return jsonify({'error': 'Failed to get execution'}), 500
    finally:
        conn.close()

@app.route('/api/executions', methods=['GET'])
@require_auth
def get_executions():
    """Get all executions for the current user"""
    workflow_id = request.args.get('workflow_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if workflow_id:
                # Verify the user owns this workflow
                cur.execute(
                    "SELECT id FROM workflows WHERE id = %s AND user_id = %s",
                    (workflow_id, session['user_id'])
                )
                if not cur.fetchone():
                    return jsonify({'error': 'Workflow not found'}), 404
                
                # Get executions for specific workflow
                cur.execute("""
                    SELECT e.*, w.name as workflow_name 
                    FROM workflow_executions e
                    JOIN workflows w ON e.workflow_id = w.id
                    WHERE e.workflow_id = %s AND w.user_id = %s
                    ORDER BY e.started_at DESC
                """, (workflow_id, session['user_id']))
            else:
                # Get all executions for user
                cur.execute("""
                    SELECT e.*, w.name as workflow_name 
                    FROM workflow_executions e
                    JOIN workflows w ON e.workflow_id = w.id
                    WHERE w.user_id = %s
                    ORDER BY e.started_at DESC
                    LIMIT 50
                """, (session['user_id'],))
            
            executions = cur.fetchall()
            
            return jsonify([dict(e) for e in executions])
            
    except Exception as e:
        app.logger.error(f"Failed to get executions: {e")
        return jsonify({'error': 'Failed to get executions'}), 500
    finally:
        conn.close()

@app.route('/api/tools', methods=['GET'])
@require_auth
def get_tools():
    """Get available tools"""
    category = request.args.get('category')
    
    # In a real implementation, this would come from a database
    # For now, we'll return a static list
    
    tools = [
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
            'id': 'slack',
            'name': 'Slack Integration',
            'description': 'Send messages to Slack channels',
            'category': 'app',
            'icon': 'fab fa-slack',
            'config': {}
        },
        {
            'id': 'email',
            'name': 'Email Integration',
            'description': 'Send emails using SMTP',
            'category': 'app',
            'icon': 'fas fa-envelope',
            'config': {}
        },
        {
            'id': 'http',
            'name': 'HTTP Request',
            'description': 'Make HTTP requests to external APIs',
            'category': 'app',
            'icon': 'fas fa-globe',
            'config': {}
        },
        {
            'id': 'pi-auth',
            'name': 'Pi Authentication',
            'description': 'Authenticate users with Pi Network',
            'category': 'app',
            'icon': 'fab fa-pi',
            'config': {}
        },
        {
            'id': 'code',
            'name': 'Code',
            'description': 'Execute custom JavaScript or Python code',
            'category': 'data',
            'icon': 'fas fa-code',
            'config': {}
        },
        {
            'id': 'set',
            'name': 'Set',
            'description': 'Set values in JSON data',
            'category': 'data',
            'icon': 'fas fa-edit',
            'config': {}
        },
        {
            'id': 'if',
            'name': 'IF Condition',
            'description': 'Conditional branching based on data',
            'category': 'logic',
            'icon': 'fas fa-question-circle',
            'config': {}
        },
        {
            'id': 'pi-payment',
            'name': 'Pi Payment',
            'description': 'Create Pi Network payments',
            'category': 'utility',
            'icon': 'fas fa-money-bill-wave',
            'config': {}
        },
        {
            'id': 'pi-data',
            'name': 'Pi Blockchain Data',
            'description': 'Read/write to Pi Blockchain',
            'category': 'utility',
            'icon': 'fas fa-database',
            'config': {}
        }
    ]
    
    if category:
        filtered_tools = [t for t in tools if t['category'] == category]
        return jsonify(filtered_tools)
    
    return jsonify(tools)

@app.route('/api/webhook/<workflow_id>', methods=['GET', 'POST', 'PUT'])
def handle_webhook(workflow_id):
    """Handle incoming webhook requests to trigger workflows"""
    # Get workflow
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM workflows WHERE id = %s AND status = 'active'",
                (workflow_id,)
            )
            workflow = cur.fetchone()
            
            if not workflow:
                return jsonify({'error': 'Workflow not found or not active'}), 404
            
            # Create execution record
            execution_id = f"exec-{uuid.uuid4().hex}"
            
            # Prepare webhook data
            webhook_data = {
                'method': request.method,
                'headers': dict(request.headers),
                'params': dict(request.args),
                'json': request.get_json(silent=True) or {},
                'form': dict(request.form) if request.form else {},
                'data': request.data.decode('utf-8') if request.data else ''
            }
            
            cur.execute(
                """INSERT INTO workflow_executions (id, workflow_id, status, started_at, results) 
                VALUES (%s, %s, %s, %s, %s)""",
                (execution_id, workflow_id, 'running', datetime.now(), json.dumps({'webhook_data': webhook_data}))
            )
            conn.commit()
            
            # In a real implementation, this would trigger the workflow execution
            # For now, we'll just return the execution ID
            
            return jsonify({
                'success': True,
                'message': 'Webhook received and workflow triggered',
                'executionId': execution_id
            })
            
    except Exception as e:
        app.logger.error(f"Webhook handling failed: {e}")
        return jsonify({'error': 'Webhook handling failed'}), 500
    finally:
        conn.close()

@app.route('/api/user/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, email, pi_uid, pi_username, created_at, last_login FROM users WHERE id = %s",
                (session['user_id'],)
            )
            user = cur.fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify(dict(user))
            
    except Exception as e:
        app.logger.error(f"Failed to get profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500
    finally:
        conn.close()

@app.route('/api/user/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    data = request.get_json()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    try:
        with conn.cursor() as cur:
            update_fields = []
            update_values = []
            
            if 'email' in data:
                update_fields.append("email = %s")
                update_values.append(data['email'])
            
            if update_fields:
                update_values.append(session['user_id'])
                cur.execute(
                    f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s",
                    update_values
                )
                conn.commit()
            
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
            
    except Exception as e:
        app.logger.error(f"Failed to update profile: {e}")
        conn.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
