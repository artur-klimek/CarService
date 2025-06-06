"""
Routes package initialization for the CarService application.

This module initializes and registers all route blueprints for the application.
It serves as the central point for route registration and ensures proper
organization of the application's URL structure.

Blueprints:
    - auth_bp: Authentication routes (login, logout, registration)
    - main_bp: Main application routes (homepage, general pages)
    - admin_bp: Administrative routes (user management, system settings)
    - employee_bp: Employee-specific routes (service management, work orders)
    - client_bp: Client-specific routes (service requests, vehicle management)

Note:
    All blueprints are registered with the Flask application in the app/__init__.py
    file. This module only imports and makes the blueprints available.

Dependencies:
    - Flask: For blueprint functionality
    - Logging: For application logging
"""

import logging
from app.routes.auth import bp as auth_bp
from app.routes.main import bp as main_bp
from app.routes.admin import bp as admin_bp
from app.routes.employee import bp as employee_bp
from app.routes.client import bp as client_bp

# Configure logging
logger = logging.getLogger(__name__)
logger.debug("Initializing routes package")

# List of all available blueprints
__all__ = ['auth_bp', 'main_bp', 'admin_bp', 'employee_bp', 'client_bp']

# Log successful blueprint imports
logger.info("Successfully imported all route blueprints")
logger.debug("Available blueprints: %s", ', '.join(__all__)) 
