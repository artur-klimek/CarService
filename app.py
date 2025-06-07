"""
Main Application Module for CarService Application.

This module serves as the entry point for the CarService application. It handles
application initialization, configuration, and server startup. The module
implements the application factory pattern for Flask and manages the application
lifecycle.

Key Features:
    - Application factory pattern implementation
    - Configuration management
    - Logging setup and initialization
    - Database initialization
    - Blueprint registration
    - Default admin account creation
    - Health check endpoint
    - Development server startup

Dependencies:
    - flask: Web framework
    - app.config: Configuration management
    - app.utils.logger: Logging utilities
    - app.models: Database models
    - app.routes: Application routes and blueprints

Note:
    The application uses debug mode for development and troubleshooting.
    Production deployments should disable debug mode and use a proper WSGI server.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from flask import Flask, Response, jsonify

from app.config import Config
from app.utils.logger import Logger
from app.models import User, db, login_manager


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    This function implements the application factory pattern for Flask. It:
    1. Initializes configuration and logging
    2. Sets up the Flask application
    3. Configures extensions (database, login manager)
    4. Registers blueprints
    5. Creates database tables
    6. Sets up default admin account if configured

    Returns:
        Flask: Configured Flask application instance

    Note:
        The application is configured with debug mode enabled for development.
        Database tables are created if they don't exist.
        A default admin account is created if configured and doesn't exist.
    """
    # Initialize configuration
    config = Config()
    logging_config = config.get_logging_config()
    server_config = config.get_server_config()
    
    # Initialize logger
    logger = Logger()
    logger.setup(
        log_dir=logging_config['log_dir'],
        level="DEBUG",  # Force DEBUG level for troubleshooting
        max_log_files=logging_config['max_log_files'],
        max_log_size_mb=logging_config['max_log_size_mb']
    )
    app_logger = logger.get_logger()
    
    app_logger.info("Starting application initialization")
    app_logger.debug(f"Server configuration: {server_config}")
    app_logger.debug(f"Logging configuration: {logging_config}")
    
    # Get absolute paths
    app_root = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(app_root, 'app', 'templates')
    static_dir = os.path.join(app_root, 'app', 'static')
    
    app_logger.debug(f"Application root directory: {app_root}")
    app_logger.debug(f"Template directory: {template_dir}")
    app_logger.debug(f"Static directory: {static_dir}")
    app_logger.debug(
        f"Template directory exists: {os.path.exists(template_dir)}"
    )
    
    # Log template directory contents for debugging
    if os.path.exists(template_dir):
        app_logger.debug("Template directory structure:")
        for root, dirs, files in os.walk(template_dir):
            app_logger.debug(f"Directory: {root}")
            app_logger.debug(f"Subdirectories: {dirs}")
            app_logger.debug(f"Files: {files}")
    else:
        app_logger.warning(f"Template directory not found: {template_dir}")
    
    # Create Flask application
    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )
    
    # Configure application
    app.config['SECRET_KEY'] = config.get_secret_key()
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True  # Enable debug mode for troubleshooting
    
    app_logger.info("Flask application created")
    app_logger.debug(f"Template folder: {app.template_folder}")
    app_logger.debug(f"Static folder: {app.static_folder}")
    app_logger.debug("Application configuration set")
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    app_logger.info("Database and login manager initialized")
    
    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.client import client_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.employee import bp as employee_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(client_bp, url_prefix='/client')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app_logger.info("Blueprints registered: main, auth, client, admin, employee")
    
    # Create database tables and default admin account
    with app.app_context():
        try:
            db.create_all()
            app_logger.info("Database tables created successfully")
        except Exception as e:
            app_logger.error(f"Failed to create database tables: {str(e)}")
            raise
        
        # Create default admin account if configured
        if config.should_create_default_admin():
            admin_config = config.get_default_admin_config()
            app_logger.debug(
                f"Checking for existing admin account: "
                f"{admin_config['username']}"
            )
            
            admin = User.query.filter_by(
                username=admin_config['username']
            ).first()
            
            if admin:
                app_logger.info(
                    f"Default admin account already exists: "
                    f"{admin_config['username']}"
                )
            else:
                try:
                    admin = User(
                        username=admin_config['username'],
                        email=admin_config['email'],
                        role='admin'
                    )
                    admin.set_password(admin_config['password'])
                    db.session.add(admin)
                    db.session.commit()
                    app_logger.info(
                        f"Default admin account created: "
                        f"{admin_config['username']}"
                    )
                except Exception as e:
                    app_logger.error(
                        f"Failed to create default admin account: {str(e)}"
                    )
                    db.session.rollback()
                    raise
    
    @app.route('/health')
    def health_check() -> Tuple[Dict[str, str], int]:
        """
        Health check endpoint for application monitoring.

        This endpoint provides a simple health check mechanism to verify
        that the application is running and responsive.

        Returns:
            Tuple[Dict[str, str], int]: JSON response with status and HTTP code
        """
        app_logger.debug("Health check endpoint called")
        return {'status': 'healthy'}, 200
    
    app_logger.info("Application initialization completed successfully")
    return app


def main() -> None:
    """
    Main function to run the application.

    This function:
    1. Initializes logging
    2. Creates the Flask application
    3. Loads server configuration
    4. Starts the development server

    Note:
        The server runs in debug mode for development and troubleshooting.
        Production deployments should use a proper WSGI server.
    """
    logger = Logger().get_logger()
    logger.info("Starting application server")
    
    try:
        app = create_app()
        config = Config()
        server_config = config.get_server_config()
        
        host = server_config['host']
        port = server_config['port']
        logger.info(f"Starting server on {host}:{port}")
        
        app.run(
            host=host,
            port=port,
            debug=True  # Force debug mode for troubleshooting
        )
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")
        raise


if __name__ == '__main__':
    main()
