"""
Role-based access control decorators for the CarService application.

This module provides decorators for enforcing role-based access control
in the application. These decorators ensure that only users with the
appropriate roles can access specific routes and functionality.

Available Decorators:
    - client_required: Restricts access to client users only
    - employee_required: Restricts access to employee users only
    - admin_required: Restricts access to admin users only

Dependencies:
    - Flask: Web framework and routing
    - Flask-Login: User session management
    - functools: Function wrapping utilities
    - logging: Application logging

Note:
    All decorators redirect unauthorized users to the main index page
    with an appropriate flash message and log the access attempt.
"""

from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
import logging

# Initialize logger
logger = logging.getLogger(__name__)

def client_required(f):
    """
    Decorator to restrict access to client users only.

    This decorator ensures that only authenticated users with the client role
    can access the decorated route. Unauthorized access attempts are logged
    and redirected to the main page.

    Args:
        f (function): The route function to decorate

    Returns:
        function: Decorated function that checks client role

    Raises:
        None: All errors are handled internally with appropriate logging

    Example:
        @bp.route('/client/dashboard')
        @login_required
        @client_required
        def client_dashboard():
            return render_template('client/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug(
            f"Client role check for {current_user.username} "
            f"from IP: {request.remote_addr}"
        )
        
        if not current_user.is_client():
            logger.warning(
                f"Unauthorized client access attempt by {current_user.username} "
                f"(ID: {current_user.id}) from IP: {request.remote_addr}"
            )
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        
        logger.debug(f"Client access granted to {current_user.username}")
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    """
    Decorator to restrict access to employee users only.

    This decorator ensures that only authenticated users with the employee role
    can access the decorated route. Unauthorized access attempts are logged
    and redirected to the main page.

    Args:
        f (function): The route function to decorate

    Returns:
        function: Decorated function that checks employee role

    Raises:
        None: All errors are handled internally with appropriate logging

    Example:
        @bp.route('/employee/dashboard')
        @login_required
        @employee_required
        def employee_dashboard():
            return render_template('employee/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug(
            f"Employee role check for {current_user.username} "
            f"from IP: {request.remote_addr}"
        )
        
        if not current_user.is_employee():
            logger.warning(
                f"Unauthorized employee access attempt by {current_user.username} "
                f"(ID: {current_user.id}) from IP: {request.remote_addr}"
            )
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        
        logger.debug(f"Employee access granted to {current_user.username}")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator to restrict access to admin users only.

    This decorator ensures that only authenticated users with the admin role
    can access the decorated route. Unauthorized access attempts are logged
    and redirected to the main page.

    Args:
        f (function): The route function to decorate

    Returns:
        function: Decorated function that checks admin role

    Raises:
        None: All errors are handled internally with appropriate logging

    Example:
        @bp.route('/admin/dashboard')
        @login_required
        @admin_required
        def admin_dashboard():
            return render_template('admin/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug(
            f"Admin role check for {current_user.username} "
            f"from IP: {request.remote_addr}"
        )
        
        if not current_user.is_admin():
            logger.warning(
                f"Unauthorized admin access attempt by {current_user.username} "
                f"(ID: {current_user.id}) from IP: {request.remote_addr}"
            )
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        
        logger.debug(f"Admin access granted to {current_user.username}")
        return f(*args, **kwargs)
    return decorated_function
