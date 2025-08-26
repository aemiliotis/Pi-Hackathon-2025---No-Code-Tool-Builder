from flask import Blueprint, jsonify, request, render_template_string
from src.models.tool import Tool, ToolExecution, db
import json
from datetime import datetime

tool_bp = Blueprint('tool', __name__)

# Helper function to verify Pi Network authentication
def verify_pi_auth(request):
    """
    In a real implementation, this would verify the Pi Network access token
    For now, we'll use a mock implementation
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    # Mock user data - in real implementation, verify with Pi Network API
    if token.startswith('mock_token_'):
        return {
            'uid': token.replace('mock_token_', 'pi_user_'),
            'username': 'PiUser' + token[-3:],
            'access_token': token
        }
    return None

# Create a new tool
@tool_bp.route('/tools', methods=['POST'])
def create_tool():
    user = verify_pi_auth(request)
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    
    try:
        tool = Tool(
            name=data.get('name'),
            description=data.get('description', ''),
            tool_type=data.get('type', 'form'),
            fields_config=data.get('fields', []),
            creator_uid=user['uid'],
            creator_name=user['username']
        )
        
        db.session.add(tool)
        db.session.commit()
        
        return jsonify(tool.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get user's tools
@tool_bp.route('/tools/my', methods=['GET'])
def get_my_tools():
    user = verify_pi_auth(request)
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    tools = Tool.query.filter_by(creator_uid=user['uid']).order_by(Tool.created_at.desc()).all()
    return jsonify([tool.to_dict() for tool in tools])

# Get public tools
@tool_bp.route('/tools/public', methods=['GET'])
def get_public_tools():
    tools = Tool.query.filter_by(published=True).order_by(Tool.created_at.desc()).all()
    return jsonify([tool.to_dict() for tool in tools])

# Get a specific tool
@tool_bp.route('/tools/<int:tool_id>', methods=['GET'])
def get_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    return jsonify(tool.to_dict())

# Update a tool
@tool_bp.route('/tools/<int:tool_id>', methods=['PUT'])
def update_tool(tool_id):
    user = verify_pi_auth(request)
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    tool = Tool.query.get_or_404(tool_id)
    
    # Check if user owns the tool
    if tool.creator_uid != user['uid']:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.json
    
    try:
        tool.name = data.get('name', tool.name)
        tool.description = data.get('description', tool.description)
        tool.tool_type = data.get('type', tool.tool_type)
        if 'fields' in data:
            tool.fields_config = json.dumps(data['fields'])
        tool.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify(tool.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a tool
@tool_bp.route('/tools/<int:tool_id>', methods=['DELETE'])
def delete_tool(tool_id):
    user = verify_pi_auth(request)
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    tool = Tool.query.get_or_404(tool_id)
    
    # Check if user owns the tool
    if tool.creator_uid != user['uid']:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # Delete associated executions first
        ToolExecution.query.filter_by(tool_id=tool_id).delete()
        db.session.delete(tool)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Publish a tool
@tool_bp.route('/tools/<int:tool_id>/publish', methods=['POST'])
def publish_tool(tool_id):
    user = verify_pi_auth(request)
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    tool = Tool.query.get_or_404(tool_id)
    
    # Check if user owns the tool
    if tool.creator_uid != user['uid']:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        tool.published = True
        tool.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(tool.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Execute a tool
@tool_bp.route('/tools/<int:tool_id>/execute', methods=['POST'])
def execute_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    
    # Only allow execution of published tools or by the creator
    user = verify_pi_auth(request)
    if not tool.published and (not user or tool.creator_uid != user['uid']):
        return jsonify({'error': 'Tool not available for execution'}), 403
    
    input_data = request.json or {}
    
    try:
        # Process the tool based on its type
        output_data = process_tool_execution(tool, input_data)
        
        # Save execution record
        execution = ToolExecution(
            tool_id=tool_id,
            input_data=input_data,
            output_data=output_data,
            user_uid=user['uid'] if user else None
        )
        db.session.add(execution)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'output': output_data,
            'execution_id': execution.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def process_tool_execution(tool, input_data):
    """Process tool execution based on tool type"""
    tool_type = tool.tool_type
    fields = json.loads(tool.fields_config) if tool.fields_config else []
    
    if tool_type == 'form':
        # For form tools, just return the submitted data with validation
        result = {
            'submitted_data': input_data,
            'message': f'Form "{tool.name}" submitted successfully!',
            'timestamp': datetime.utcnow().isoformat()
        }
        return result
    
    elif tool_type == 'calculator':
        # Enhanced calculator logic with more operations
        try:
            expression = input_data.get('expression', '')
            # Basic safety check - only allow numbers and basic operators
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return {
                    'expression': expression,
                    'result': result,
                    'message': f'Calculation completed: {expression} = {result}'
                }
            else:
                return {'error': 'Invalid expression. Only numbers and basic operators (+, -, *, /, parentheses) are allowed.'}
        except Exception as e:
            return {'error': f'Calculation error: {str(e)}'}
    
    elif tool_type == 'converter':
        # Enhanced unit converter with multiple conversion types
        from_unit = input_data.get('from_unit')
        to_unit = input_data.get('to_unit')
        value = float(input_data.get('value', 0))
        
        # Temperature conversions
        if from_unit == 'celsius' and to_unit == 'fahrenheit':
            result = (value * 9/5) + 32
        elif from_unit == 'fahrenheit' and to_unit == 'celsius':
            result = (value - 32) * 5/9
        elif from_unit == 'celsius' and to_unit == 'kelvin':
            result = value + 273.15
        elif from_unit == 'kelvin' and to_unit == 'celsius':
            result = value - 273.15
        elif from_unit == 'fahrenheit' and to_unit == 'kelvin':
            result = (value - 32) * 5/9 + 273.15
        elif from_unit == 'kelvin' and to_unit == 'fahrenheit':
            result = (value - 273.15) * 9/5 + 32
        
        # Length conversions
        elif from_unit == 'meters' and to_unit == 'feet':
            result = value * 3.28084
        elif from_unit == 'feet' and to_unit == 'meters':
            result = value / 3.28084
        elif from_unit == 'kilometers' and to_unit == 'miles':
            result = value * 0.621371
        elif from_unit == 'miles' and to_unit == 'kilometers':
            result = value / 0.621371
        
        # Weight conversions
        elif from_unit == 'kilograms' and to_unit == 'pounds':
            result = value * 2.20462
        elif from_unit == 'pounds' and to_unit == 'kilograms':
            result = value / 2.20462
        
        else:
            result = value  # Default: no conversion
        
        return {
            'original_value': value,
            'from_unit': from_unit,
            'to_unit': to_unit,
            'converted_value': round(result, 4),
            'message': f'Converted {value} {from_unit} to {round(result, 4)} {to_unit}'
        }
    
    elif tool_type == 'generator':
        # Enhanced text generator with templates
        template = input_data.get('template', 'Hello, {name}!')
        variables = input_data.get('variables', {})
        
        try:
            generated_text = template.format(**variables)
            return {
                'template': template,
                'variables': variables,
                'generated_text': generated_text,
                'message': 'Text generated successfully!'
            }
        except Exception as e:
            return {'error': f'Generation error: {str(e)}'}
    
    elif tool_type == 'survey':
        # Survey tool for collecting feedback
        responses = input_data.get('responses', {})
        rating = input_data.get('rating', 0)
        
        return {
            'responses': responses,
            'rating': rating,
            'message': f'Survey completed! Thank you for your feedback.',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    elif tool_type == 'quiz':
        # Quiz tool with scoring
        answers = input_data.get('answers', {})
        correct_answers = input_data.get('correct_answers', {})
        
        score = 0
        total = len(correct_answers)
        
        for question, correct in correct_answers.items():
            if answers.get(question) == correct:
                score += 1
        
        percentage = (score / total * 100) if total > 0 else 0
        
        return {
            'score': score,
            'total': total,
            'percentage': round(percentage, 1),
            'message': f'Quiz completed! You scored {score}/{total} ({percentage:.1f}%)',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    elif tool_type == 'poll':
        # Simple polling tool
        vote = input_data.get('vote', '')
        voter_id = input_data.get('voter_id', 'anonymous')
        
        return {
            'vote': vote,
            'voter_id': voter_id,
            'message': f'Thank you for voting for: {vote}',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    elif tool_type == 'scheduler':
        # Event scheduling tool
        event_name = input_data.get('event_name', '')
        event_date = input_data.get('event_date', '')
        event_time = input_data.get('event_time', '')
        attendees = input_data.get('attendees', [])
        
        return {
            'event_name': event_name,
            'event_date': event_date,
            'event_time': event_time,
            'attendees': attendees,
            'message': f'Event "{event_name}" scheduled for {event_date} at {event_time}',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    elif tool_type == 'tracker':
        # Progress/habit tracker
        activity = input_data.get('activity', '')
        value = input_data.get('value', 0)
        unit = input_data.get('unit', '')
        notes = input_data.get('notes', '')
        
        return {
            'activity': activity,
            'value': value,
            'unit': unit,
            'notes': notes,
            'message': f'Tracked: {value} {unit} for {activity}',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    elif tool_type == 'validator':
        # Data validation tool
        data_to_validate = input_data.get('data', '')
        validation_type = input_data.get('type', 'email')
        
        import re
        
        if validation_type == 'email':
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            is_valid = bool(re.match(pattern, data_to_validate))
            message = f'Email address is {"valid" if is_valid else "invalid"}'
        elif validation_type == 'phone':
            pattern = r'^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'
            is_valid = bool(re.match(pattern, data_to_validate))
            message = f'Phone number is {"valid" if is_valid else "invalid"}'
        elif validation_type == 'url':
            pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
            is_valid = bool(re.match(pattern, data_to_validate))
            message = f'URL is {"valid" if is_valid else "invalid"}'
        else:
            is_valid = False
            message = 'Unknown validation type'
        
        return {
            'data': data_to_validate,
            'validation_type': validation_type,
            'is_valid': is_valid,
            'message': message
        }
    
    else:
        return {'error': f'Unknown tool type: {tool_type}'}

# Serve tool execution page
@tool_bp.route('/tool/<int:tool_id>')
def serve_tool_page(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    
    # Only serve published tools
    if not tool.published:
        return "Tool not available", 404
    
    # Generate HTML for the tool
    tool_html = generate_tool_html(tool)
    return tool_html

def generate_tool_html(tool):
    """Generate HTML for tool execution"""
    fields = json.loads(tool.fields_config) if tool.fields_config else []
    
    if tool.tool_type == 'form':
        form_fields_html = ''
        for field in fields:
            if not field.get('label'):
                continue
                
            field_html = f'<div class="form-group"><label>{field["label"]}</label>'
            
            if field['type'] == 'textarea':
                field_html += f'<textarea name="{field["id"]}" rows="3"></textarea>'
            elif field['type'] == 'select':
                field_html += f'<select name="{field["id"]}"><option>Option 1</option><option>Option 2</option></select>'
            else:
                field_html += f'<input type="{field["type"]}" name="{field["id"]}">'
            
            field_html += '</div>'
            form_fields_html += field_html
    
    elif tool.tool_type == 'calculator':
        form_fields_html = '''
            <div class="form-group">
                <label>Mathematical Expression</label>
                <input type="text" name="expression" placeholder="e.g., 2 + 2 * 3, (10 + 5) / 3">
                <small>Supported operations: +, -, *, /, parentheses</small>
            </div>
        '''
    
    elif tool.tool_type == 'converter':
        form_fields_html = '''
            <div class="form-group">
                <label>Value to Convert</label>
                <input type="number" name="value" step="any" placeholder="Enter value">
            </div>
            <div class="form-group">
                <label>From Unit</label>
                <select name="from_unit">
                    <optgroup label="Temperature">
                        <option value="celsius">Celsius</option>
                        <option value="fahrenheit">Fahrenheit</option>
                        <option value="kelvin">Kelvin</option>
                    </optgroup>
                    <optgroup label="Length">
                        <option value="meters">Meters</option>
                        <option value="feet">Feet</option>
                        <option value="kilometers">Kilometers</option>
                        <option value="miles">Miles</option>
                    </optgroup>
                    <optgroup label="Weight">
                        <option value="kilograms">Kilograms</option>
                        <option value="pounds">Pounds</option>
                    </optgroup>
                </select>
            </div>
            <div class="form-group">
                <label>To Unit</label>
                <select name="to_unit">
                    <optgroup label="Temperature">
                        <option value="fahrenheit">Fahrenheit</option>
                        <option value="celsius">Celsius</option>
                        <option value="kelvin">Kelvin</option>
                    </optgroup>
                    <optgroup label="Length">
                        <option value="feet">Feet</option>
                        <option value="meters">Meters</option>
                        <option value="miles">Miles</option>
                        <option value="kilometers">Kilometers</option>
                    </optgroup>
                    <optgroup label="Weight">
                        <option value="pounds">Pounds</option>
                        <option value="kilograms">Kilograms</option>
                    </optgroup>
                </select>
            </div>
        '''
    
    elif tool.tool_type == 'generator':
        form_fields_html = '''
            <div class="form-group">
                <label>Template Text</label>
                <textarea name="template" rows="4" placeholder="Hello, {name}! Welcome to {place}. Your order #{order_id} is ready."></textarea>
                <small>Use {variable_name} for placeholders</small>
            </div>
            <div class="form-group">
                <label>Variables (JSON format)</label>
                <textarea name="variables" rows="4" placeholder='{"name": "John", "place": "Pi Network", "order_id": "12345"}'></textarea>
                <small>Enter variables in JSON format</small>
            </div>
        '''
    
    elif tool.tool_type == 'survey':
        form_fields_html = '''
            <div class="form-group">
                <label>Overall Rating (1-5)</label>
                <select name="rating">
                    <option value="1">1 - Poor</option>
                    <option value="2">2 - Fair</option>
                    <option value="3">3 - Good</option>
                    <option value="4">4 - Very Good</option>
                    <option value="5">5 - Excellent</option>
                </select>
            </div>
            <div class="form-group">
                <label>Comments</label>
                <textarea name="responses[comments]" rows="4" placeholder="Please share your feedback..."></textarea>
            </div>
            <div class="form-group">
                <label>Would you recommend this?</label>
                <select name="responses[recommend]">
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                    <option value="maybe">Maybe</option>
                </select>
            </div>
        '''
    
    elif tool.tool_type == 'quiz':
        form_fields_html = '''
            <div class="form-group">
                <label>Question 1: What is 2 + 2?</label>
                <select name="answers[q1]">
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                </select>
            </div>
            <div class="form-group">
                <label>Question 2: What is the capital of France?</label>
                <select name="answers[q2]">
                    <option value="London">London</option>
                    <option value="Paris">Paris</option>
                    <option value="Berlin">Berlin</option>
                </select>
            </div>
            <input type="hidden" name="correct_answers" value='{"q1": "4", "q2": "Paris"}'>
        '''
    
    elif tool.tool_type == 'poll':
        form_fields_html = '''
            <div class="form-group">
                <label>What is your favorite Pi Network feature?</label>
                <select name="vote">
                    <option value="mining">Mining</option>
                    <option value="apps">Pi Apps</option>
                    <option value="wallet">Pi Wallet</option>
                    <option value="community">Community</option>
                </select>
            </div>
            <div class="form-group">
                <label>Your ID (optional)</label>
                <input type="text" name="voter_id" placeholder="Enter your identifier">
            </div>
        '''
    
    elif tool.tool_type == 'scheduler':
        form_fields_html = '''
            <div class="form-group">
                <label>Event Name</label>
                <input type="text" name="event_name" placeholder="Enter event name">
            </div>
            <div class="form-group">
                <label>Event Date</label>
                <input type="date" name="event_date">
            </div>
            <div class="form-group">
                <label>Event Time</label>
                <input type="time" name="event_time">
            </div>
            <div class="form-group">
                <label>Attendees (comma-separated)</label>
                <textarea name="attendees" rows="3" placeholder="john@example.com, jane@example.com"></textarea>
            </div>
        '''
    
    elif tool.tool_type == 'tracker':
        form_fields_html = '''
            <div class="form-group">
                <label>Activity</label>
                <input type="text" name="activity" placeholder="e.g., Exercise, Reading, Work">
            </div>
            <div class="form-group">
                <label>Value</label>
                <input type="number" name="value" step="any" placeholder="Enter amount">
            </div>
            <div class="form-group">
                <label>Unit</label>
                <input type="text" name="unit" placeholder="e.g., minutes, pages, hours">
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea name="notes" rows="3" placeholder="Additional notes..."></textarea>
            </div>
        '''
    
    elif tool.tool_type == 'validator':
        form_fields_html = '''
            <div class="form-group">
                <label>Data to Validate</label>
                <input type="text" name="data" placeholder="Enter data to validate">
            </div>
            <div class="form-group">
                <label>Validation Type</label>
                <select name="type">
                    <option value="email">Email Address</option>
                    <option value="phone">Phone Number</option>
                    <option value="url">URL</option>
                </select>
            </div>
        '''
    
    else:
        form_fields_html = '<p>Tool type not supported for direct execution.</p>'
    
    html_template = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tool.name} - Pi No-Code Tool</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            h1 {{ color: #667eea; margin-bottom: 10px; }}
            .description {{ color: #666; margin-bottom: 30px; font-size: 1.1rem; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #555; }}
            .form-group input, .form-group textarea, .form-group select {{ width: 100%; padding: 12px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 1rem; }}
            .form-group input:focus, .form-group textarea:focus, .form-group select:focus {{ outline: none; border-color: #667eea; }}
            .btn {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }}
            .btn:hover {{ transform: translateY(-2px); }}
            .result {{ margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #667eea; }}
            .error {{ background: #f8d7da; border-left-color: #dc3545; color: #721c24; }}
            .success {{ background: #d4edda; border-left-color: #28a745; color: #155724; }}
            .creator-info {{ margin-top: 30px; padding: 15px; background: #e8f4f8; border-radius: 8px; font-size: 0.9rem; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛠️ {tool.name}</h1>
            <p class="description">{tool.description}</p>
            
            <form id="tool-form">
                {form_fields_html}
                <button type="submit" class="btn">Execute Tool</button>
            </form>
            
            <div id="result" class="result" style="display: none;"></div>
            
            <div class="creator-info">
                <strong>Created by:</strong> {tool.creator_name} | <strong>Tool Type:</strong> {tool.tool_type.title()}
            </div>
        </div>
        
        <script>
            document.getElementById('tool-form').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = {{}};
                
                for (let [key, value] of formData.entries()) {{
                    if (key === 'variables' && value) {{
                        try {{
                            data[key] = JSON.parse(value);
                        }} catch (e) {{
                            showResult('Invalid JSON format for variables', 'error');
                            return;
                        }}
                    }} else {{
                        data[key] = value;
                    }}
                }}
                
                try {{
                    const response = await fetch('/api/tools/{tool.id}/execute', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        showResult(formatOutput(result.output), 'success');
                    }} else {{
                        showResult(result.error || 'Execution failed', 'error');
                    }}
                }} catch (error) {{
                    showResult('Network error: ' + error.message, 'error');
                }}
            }});
            
            function showResult(content, type) {{
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = content;
                resultDiv.className = 'result ' + type;
                resultDiv.style.display = 'block';
                resultDiv.scrollIntoView({{ behavior: 'smooth' }});
            }}
            
            function formatOutput(output) {{
                if (typeof output === 'object') {{
                    let html = '';
                    for (let [key, value] of Object.entries(output)) {{
                        if (key === 'message') {{
                            html += '<h3>' + value + '</h3>';
                        }} else if (key === 'generated_text') {{
                            html += '<h4>Generated Text:</h4><p style="font-size: 1.1rem; font-weight: bold;">' + value + '</p>';
                        }} else if (key === 'result') {{
                            html += '<h4>Result:</h4><p style="font-size: 1.5rem; font-weight: bold; color: #667eea;">' + value + '</p>';
                        }} else if (key === 'converted_value') {{
                            html += '<h4>Converted Value:</h4><p style="font-size: 1.3rem; font-weight: bold; color: #667eea;">' + value + '</p>';
                        }} else {{
                            html += '<p><strong>' + key.replace('_', ' ').toUpperCase() + ':</strong> ' + JSON.stringify(value) + '</p>';
                        }}
                    }}
                    return html;
                }} else {{
                    return '<p>' + output + '</p>';
                }}
            }}
        </script>
    </body>
    </html>
    '''
    
    return html_template

