"""
CarService Application Initialization Module.

This module handles the initialization and configuration of the CarService Flask application.
It sets up the database, authentication, and other core components of the application.

Key Components:
    - Flask application creation and configuration
    - Database initialization (SQLAlchemy)
    - Authentication setup (LoginManager)
    - Database migrations (Flask-Migrate)
    - Default user creation
    - Blueprint registration

Dependencies:
    - Flask
    - Flask-SQLAlchemy
    - Flask-Login
    - Flask-Migrate
    - app.config.Config

Note:
    This module implements the application factory pattern and handles
    the creation of default users based on configuration settings.
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from app.config import Config

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_default_users(app):
    """
    Create default users if enabled in configuration.

    This function creates default admin, client, and employee users based on
    the application configuration. It ensures that the database tables exist
    and handles both creation and updates of default users.

    Args:
        app (Flask): The Flask application instance.

    Note:
        - Only creates users if their respective configuration is enabled
        - Updates existing users if they already exist
        - Commits all changes to the database
        - Logs all user creation and update operations
    """
    from app.models import User
    from app import db
    
    logger.info("Starting default user creation process")
    
    with app.app_context():
        try:
            # Ensure database tables are created
            db.create_all()
            db.session.commit()
            logger.debug("Database tables created/verified successfully")
            
            # Create default admin if enabled
            if app.config.get('DEFAULT_ADMIN', {}).get('enabled'):
                admin = User.query.filter_by(
                    username=app.config['DEFAULT_ADMIN']['username']
                ).first()
                
                if not admin:
                    admin = User(
                        username=app.config['DEFAULT_ADMIN']['username'],
                        email=app.config['DEFAULT_ADMIN']['email'],
                        role='admin'
                    )
                    admin.set_password(app.config['DEFAULT_ADMIN']['password'])
                    db.session.add(admin)
                    logger.info(
                        f"Created default admin user: {admin.username} "
                        f"(email: {admin.email})"
                    )
                else:
                    admin.email = app.config['DEFAULT_ADMIN']['email']
                    admin.set_password(app.config['DEFAULT_ADMIN']['password'])
                    logger.info(
                        f"Updated default admin user: {admin.username} "
                        f"(email: {admin.email})"
                    )

            # Create default client if enabled
            if app.config.get('DEFAULT_CLIENT', {}).get('enabled'):
                client = User.query.filter_by(
                    username=app.config['DEFAULT_CLIENT']['username']
                ).first()
                
                if not client:
                    client = User(
                        username=app.config['DEFAULT_CLIENT']['username'],
                        email=app.config['DEFAULT_CLIENT']['email'],
                        role='client'
                    )
                    client.set_password(app.config['DEFAULT_CLIENT']['password'])
                    db.session.add(client)
                    logger.info(
                        f"Created default client user: {client.username} "
                        f"(email: {client.email})"
                    )
                else:
                    client.email = app.config['DEFAULT_CLIENT']['email']
                    client.set_password(app.config['DEFAULT_CLIENT']['password'])
                    logger.info(
                        f"Updated default client user: {client.username} "
                        f"(email: {client.email})"
                    )

            # Create default employee if enabled
            if app.config.get('DEFAULT_EMPLOYEE', {}).get('enabled'):
                employee = User.query.filter_by(
                    username=app.config['DEFAULT_EMPLOYEE']['username']
                ).first()
                
                if not employee:
                    employee = User(
                        username=app.config['DEFAULT_EMPLOYEE']['username'],
                        email=app.config['DEFAULT_EMPLOYEE']['email'],
                        role='employee'
                    )
                    employee.set_password(app.config['DEFAULT_EMPLOYEE']['password'])
                    db.session.add(employee)
                    logger.info(
                        f"Created default employee user: {employee.username} "
                        f"(email: {employee.email})"
                    )
                else:
                    employee.email = app.config['DEFAULT_EMPLOYEE']['email']
                    employee.set_password(app.config['DEFAULT_EMPLOYEE']['password'])
                    logger.info(
                        f"Updated default employee user: {employee.username} "
                        f"(email: {employee.email})"
                    )

            db.session.commit()
            logger.info("Default user creation process completed successfully")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during default user creation: {str(e)}")
            raise


def create_app(config_class=Config):
    """
    Create and configure the Flask application.

    This function implements the application factory pattern, creating and
    configuring a new Flask application instance with all necessary extensions
    and settings.

    Args:
        config_class (class): Configuration class to use for the application.
            Defaults to Config.

    Returns:
        Flask: The configured Flask application instance.

    Note:
        - Initializes all Flask extensions
        - Sets up database and migrations
        - Configures authentication
        - Creates default users
        - Registers all blueprints
    """
    logger.info("Initializing Flask application")
    
    app = Flask(__name__)
    
    # Initialize configuration
    config = config_class()
    app.config.update(
        SECRET_KEY=config.SECRET_KEY,
        SQLALCHEMY_DATABASE_URI=config.SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=config.SQLALCHEMY_TRACK_MODIFICATIONS,
        DEFAULT_ADMIN=config.DEFAULT_ADMIN,
        DEFAULT_CLIENT=config.DEFAULT_CLIENT,
        DEFAULT_EMPLOYEE=config.DEFAULT_EMPLOYEE
    )
    logger.debug("Application configuration loaded")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    logger.debug("Flask extensions initialized")
    
    # Create database tables and default users
    with app.app_context():
        try:
            create_default_users(app)
            logger.info("Database initialization completed")
        except Exception as e:
            logger.error(f"Error during database initialization: {str(e)}")
            raise

    # Register blueprints
    from app.routes import auth_bp, main_bp, admin_bp, employee_bp, client_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(client_bp, url_prefix='/client')
    logger.info("All blueprints registered successfully")

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    logger.debug("Login manager configured")

    logger.info("Flask application initialization completed successfully")
    return app
