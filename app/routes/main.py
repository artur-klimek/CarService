"""
Main routes for the CarService application.

This module handles the core application routes including:
- Home page (index)
- Contact form
- Dashboard redirection based on user roles

Routes:
    - /: Home page
    - /contact: Contact form page
    - /dashboard: Role-based dashboard redirection

Dependencies:
    - Flask: Web framework and routing
    - Flask-Login: User session management
    - WTForms: Form handling and validation
    - Custom Logger: Application logging utility

Note:
    The contact form submission is currently a placeholder (TODO).
    Future implementation should include actual email sending or message storage.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app.utils.logger import Logger
from app.forms import ContactForm
import logging

# Initialize blueprint and logger
bp = Blueprint('main', __name__)
logger = Logger().get_logger()

@bp.route('/')
def index():
    """
    Render the application's home page.

    This route serves as the main entry point to the application,
    displaying the landing page with general information about
    the car service.

    Returns:
        str: Rendered home page template

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info("Home page accessed")
    logger.debug(f"Home page access from IP: {request.remote_addr}")
    
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        flash('Error loading home page', 'error')
        return render_template('index.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Handle the contact form page and submissions.

    This route manages both the display of the contact form and
    the processing of form submissions. Currently, form submission
    is a placeholder and needs to be implemented.

    Methods:
        GET: Display the contact form
        POST: Process form submission (placeholder)

    Returns:
        GET: Rendered contact form template
        POST: Redirect to home page on successful submission

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info("Contact page accessed")
    logger.debug(f"Contact page access from IP: {request.remote_addr}")
    
    try:
        form = ContactForm()
        
        if form.validate_on_submit():
            logger.info(
                f"Contact form submitted by {form.name.data} "
                f"(email: {form.email.data})"
            )
            logger.debug(f"Contact message: {form.message.data[:100]}...")
            
            # TODO: Implement contact form submission
            # This should include:
            # - Email sending
            # - Message storage
            # - Notification system
            
            flash('Your message has been sent. We will contact you soon.', 'success')
            return redirect(url_for('main.index'))
        
        return render_template('contact.html', form=form)
    except Exception as e:
        logger.error(f"Error in contact form: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
        return render_template('contact.html', form=form)

@bp.route('/dashboard')
def dashboard():
    """
    Redirect users to their role-specific dashboard.

    This route acts as a central dashboard router that:
    - Checks user authentication
    - Determines user role
    - Redirects to appropriate dashboard

    Returns:
        redirect: Role-specific dashboard URL
            - Admin dashboard for administrators
            - Employee dashboard for employees
            - Client dashboard for clients
            - Login page for unauthenticated users

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info("Dashboard router accessed")
    logger.debug(f"Dashboard router access from IP: {request.remote_addr}")
    
    try:
        if not current_user.is_authenticated:
            logger.info("Unauthenticated user redirected to login")
            return redirect(url_for('auth.login'))
        
        # Log user role and redirect accordingly
        if current_user.is_admin():
            logger.info(f"Admin user {current_user.username} redirected to admin dashboard")
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_employee():
            logger.info(f"Employee {current_user.username} redirected to employee dashboard")
            return redirect(url_for('employee.dashboard'))
        else:
            logger.info(f"Client {current_user.username} redirected to client dashboard")
            return redirect(url_for('client.dashboard'))
    except Exception as e:
        logger.error(f"Error in dashboard routing: {str(e)}")
        flash('Error accessing dashboard', 'error')
        return redirect(url_for('main.index'))
