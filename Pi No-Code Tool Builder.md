# Pi No-Code Tool Builder

A comprehensive no-code tool builder application designed for the Pi Hackathon 2025. This application allows users to create, manage, and share tools without writing any code, all integrated with the Pi Network ecosystem.

## 🌟 Features

### Core Functionality
- **Visual Tool Builder**: Drag-and-drop interface for creating tools
- **Live Preview**: Real-time preview of tools being built
- **Multiple Tool Types**: Support for forms, calculators, converters, and text generators
- **Pi Network Integration**: Authentication and branding aligned with Pi Network
- **Public Tool Execution**: Each tool gets its own shareable URL
- **User Management**: Complete user authentication and tool ownership system

### Tool Types Supported
1. **Form Tools**: Create custom forms with various field types
2. **Calculators**: Build simple calculation tools
3. **Unit Converters**: Create conversion utilities
4. **Text Generators**: Build template-based text generation tools

### Field Types Available
- Text Input
- Number Input
- Email Input
- Text Area
- Dropdown/Select

## 🏗️ Architecture

### Backend (Flask)
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite for development (easily upgradeable to PostgreSQL)
- **API**: RESTful API with CORS support
- **Authentication**: Pi Network integration framework (mock implementation)

### Frontend
- **Technology**: Vanilla HTML/CSS/JavaScript
- **Design**: Modern, responsive interface with Pi Network branding
- **Features**: Tab navigation, live preview, form builder

### Database Schema
- **Tools**: Store tool configurations and metadata
- **Tool Executions**: Track tool usage and results
- **Users**: Pi Network user integration

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Virtual environment support

### Installation
1. Navigate to the project directory:
   ```bash
   cd pi-nocode-builder
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies (already installed):
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python src/main.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
pi-nocode-builder/
├── src/
│   ├── main.py              # Main Flask application
│   ├── models/
│   │   ├── user.py          # User model
│   │   └── tool.py          # Tool and ToolExecution models
│   ├── routes/
│   │   ├── user.py          # User API routes
│   │   └── tool.py          # Tool API routes
│   ├── static/
│   │   └── index.html       # Frontend application
│   └── database/
│       └── app.db           # SQLite database
├── venv/                    # Virtual environment
└── requirements.txt         # Python dependencies
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/login` - Pi Network login (mock)
- `POST /api/auth/logout` - User logout

### Tools Management
- `GET /api/tools/my` - Get user's tools
- `GET /api/tools/public` - Get public tools
- `POST /api/tools` - Create new tool
- `GET /api/tools/{id}` - Get specific tool
- `PUT /api/tools/{id}` - Update tool
- `DELETE /api/tools/{id}` - Delete tool
- `POST /api/tools/{id}/publish` - Publish tool
- `POST /api/tools/{id}/execute` - Execute tool

### Public Tool Access
- `GET /tool/{id}` - Access public tool execution page

## 🎨 User Interface

### Main Sections
1. **Tool Builder**: Visual interface for creating tools
2. **My Tools**: Manage created tools
3. **Explore Tools**: Browse public tools

### Key Features
- **Live Preview**: See tools as you build them
- **Field Management**: Add, remove, and configure form fields
- **Tool Publishing**: Make tools available to the public
- **Responsive Design**: Works on desktop and mobile

## 🔐 Pi Network Integration

### Current Implementation
- Mock Pi Network authentication
- Pi Network branding and styling
- User session management
- Ready for real Pi SDK integration

### For Production
Replace the mock authentication in `src/routes/tool.py` with actual Pi Network SDK calls:

```python
def verify_pi_auth(request):
    # Replace with actual Pi Network SDK verification
    # Example:
    # from pi_sdk import verify_token
    # return verify_token(request.headers.get('Authorization'))
    pass
```

## 🛠️ Development

### Adding New Tool Types
1. Update the tool type options in `index.html`
2. Add processing logic in `process_tool_execution()` in `tool.py`
3. Update the HTML generation in `generate_tool_html()`

### Customizing Styling
- Modify CSS in `src/static/index.html`
- Update Pi Network branding colors and fonts
- Adjust responsive breakpoints

### Database Migrations
For production deployment:
1. Replace SQLite with PostgreSQL
2. Add proper database migration system
3. Implement backup and recovery procedures

## 🚀 Deployment

### Local Testing
The application runs on `http://localhost:5000` and is ready for local testing.

### Production Deployment
1. Update database configuration for production
2. Configure environment variables
3. Set up proper Pi Network SDK integration
4. Deploy using a WSGI server (Gunicorn, uWSGI)

## 📋 Pi Hackathon 2025 Compliance

### Requirements Met
- ✅ **Pi Authentication**: Framework ready for Pi SDK
- ✅ **Pi-Only Transactions**: No external payment systems
- ✅ **Professional UI**: Modern, clean interface
- ✅ **No Trademark Violations**: Proper Pi Network branding
- ✅ **Limited Data Collection**: Only essential tool data
- ✅ **No External Redirects**: All functionality within Pi ecosystem

### Hackathon Submission Checklist
- ✅ Complete application functionality
- ✅ Pi Network integration framework
- ✅ Professional user interface
- ✅ Tool creation and execution system
- ✅ Public tool sharing capability
- ✅ Database persistence
- ✅ Responsive design

## 🤝 Contributing

This project is designed for the Pi Hackathon 2025. Future enhancements could include:
- Advanced tool templates
- Collaboration features
- Analytics dashboard
- Mobile app version
- Advanced field validation
- Tool marketplace features

## 📄 License

This project is created for the Pi Hackathon 2025 competition.

## 🆘 Support

For questions or issues:
1. Check the console logs for error messages
2. Verify database connectivity
3. Ensure all dependencies are installed
4. Test API endpoints individually

---

**Built with ❤️ for the Pi Network Community**

