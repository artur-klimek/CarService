"""
Authentication routes for the CarService application.

This module handles all authentication-related functionality including:
- User login and logout
- User registration
- Session management
- Access control

Routes:
    - /login: User authentication
    - /logout: User session termination
    - /register: New user registration

Dependencies:
    - Flask: Web framework and routing
    - Flask-Login: User session management
    - SQLAlchemy: Database operations
    - WTForms: Form handling and validation
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm
from app.utils.logger import Logger
import logging

# Initialize blueprint and logger
bp = Blueprint('auth', __name__)
logger = Logger().get_logger()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login functionality.

    This route manages user authentication through a login form.
    It validates user credentials and creates a user session upon
    successful authentication.

    Methods:
        GET: Display login form
        POST: Process login form submission

    Returns:
        GET: Rendered login template
        POST: Redirect to next page or main index on success,
              redirect to login page with error on failure

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    if request.method == 'GET':
        logger.info("Accessing login page")
        logger.debug("Login page accessed from IP: %s", request.remote_addr)
    else:
        logger.info("Login attempt")
        logger.debug("Login attempt from IP: %s", request.remote_addr)
    
    form = LoginForm()
    if form.validate_on_submit():
        logger.info(f"Login attempt for username: {form.username.data}")
        logger.debug("Processing login form submission")
        
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'danger')
                logger.warning(
                    f"Failed login attempt for username: {form.username.data} "
                    f"from IP: {request.remote_addr}"
                )
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            logger.info(
                f"User {user.username} (ID: {user.id}) logged in successfully"
            )
            logger.debug(
                f"User {user.username} session created with remember_me={form.remember_me.data}"
            )
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
                logger.debug(f"Redirecting to default next page: {next_page}")
            else:
                logger.debug(f"Redirecting to requested next page: {next_page}")
            
            return redirect(next_page)
        except Exception as e:
            logger.error(f"Error during login process: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """
    Handle user logout functionality.

    This route terminates the current user's session and redirects
    to the main page. It requires an active user session.

    Returns:
        Redirect to main index page

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    try:
        username = current_user.username
        user_id = current_user.id
        logger.info(f"User {username} (ID: {user_id}) logged out")
        logger.debug(f"Logout request from IP: {request.remote_addr}")
        
        logout_user()
        logger.debug(f"User session terminated for {username}")
        
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"Error during logout process: {str(e)}")
        flash('An error occurred during logout. Please try again.', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle new user registration.

    This route manages the user registration process through a
    registration form. It creates new user accounts with the
    default 'client' role.

    Methods:
        GET: Display registration form
        POST: Process registration form submission

    Returns:
        GET: Rendered registration template
        POST: Redirect to login page on success,
              redirect to registration page with error on failure

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    if request.method == 'GET':
        logger.info("Accessing registration page")
        logger.debug("Registration page accessed from IP: %s", request.remote_addr)
    else:
        logger.info("Registration attempt")
        logger.debug("Registration attempt from IP: %s", request.remote_addr)
    
    form = RegistrationForm()
    if form.validate_on_submit():
        logger.info(f"Registration attempt for username: {form.username.data}")
        logger.debug("Processing registration form submission")
        
        try:
            # Check if username or email already exists
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists', 'danger')
                logger.warning(
                    f"Registration failed - username already exists: {form.username.data}"
                )
                return redirect(url_for('auth.register'))
            
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered', 'danger')
                logger.warning(
                    f"Registration failed - email already registered: {form.email.data}"
                )
                return redirect(url_for('auth.register'))
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                role='client'  # Default role for new users
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Congratulations, you are now registered!', 'success')
            logger.info(
                f"New user registered: {user.username} (ID: {user.id})"
            )
            logger.debug(
                f"User {user.username} created with role: {user.role}"
            )
            
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration process: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html', form=form)
