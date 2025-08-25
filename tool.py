from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Tool(db.Model):
    __tablename__ = 'tools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    tool_type = db.Column(db.String(50), nullable=False)  # form, calculator, converter, generator
    fields_config = db.Column(db.Text)  # JSON string of field configurations
    creator_uid = db.Column(db.String(100), nullable=False)  # Pi Network user ID
    creator_name = db.Column(db.String(100), nullable=False)  # Pi Network username
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, description, tool_type, fields_config, creator_uid, creator_name):
        self.name = name
        self.description = description
        self.tool_type = tool_type
        self.fields_config = json.dumps(fields_config) if isinstance(fields_config, (list, dict)) else fields_config
        self.creator_uid = creator_uid
        self.creator_name = creator_name
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.tool_type,
            'fields': json.loads(self.fields_config) if self.fields_config else [],
            'creator_uid': self.creator_uid,
            'creator_name': self.creator_name,
            'published': self.published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ToolExecution(db.Model):
    __tablename__ = 'tool_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    user_uid = db.Column(db.String(100))  # Optional - for tracking usage
    input_data = db.Column(db.Text)  # JSON string of input data
    output_data = db.Column(db.Text)  # JSON string of output data
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tool = db.relationship('Tool', backref=db.backref('executions', lazy=True))
    
    def __init__(self, tool_id, input_data, output_data, user_uid=None):
        self.tool_id = tool_id
        self.input_data = json.dumps(input_data) if isinstance(input_data, (list, dict)) else input_data
        self.output_data = json.dumps(output_data) if isinstance(output_data, (list, dict)) else output_data
        self.user_uid = user_uid
    
    def to_dict(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'user_uid': self.user_uid,
            'input_data': json.loads(self.input_data) if self.input_data else {},
            'output_data': json.loads(self.output_data) if self.output_data else {},
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }

