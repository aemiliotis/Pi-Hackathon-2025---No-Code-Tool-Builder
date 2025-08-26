from flask import Blueprint, jsonify, request
from user import User
from tool import db # Import db from a common location

user_bp = Blueprint("user", __name__)

@user_bp.route("/auth/login", methods=["POST"])
def login():
    """Mock Pi Network login"""
    try:
        data = request.get_json()
        
        # Mock Pi Network authentication
        username = data.get('username', 'PiUser169')
        pi_token = data.get('pi_token', 'mock_pi_token_12345')
        
        # In a real implementation, verify the Pi token with Pi Network API
        if pi_token.startswith('mock_pi_token_'):
            user_data = {
                'username': username,
                'pi_token': pi_token,
                'uid': 'pi_user_' + username.lower()
            }
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid Pi Network token'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500

@user_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Logout failed: {str(e)}'
        }), 500

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
