"""
Utility modules for the CarService application.

This module serves as the entry point for utility functions and decorators
used throughout the application. It provides role-based access control
decorators and other utility functions.

Available Decorators:
    - client_required: Ensures the user has client role
    - employee_required: Ensures the user has employee role
    - admin_required: Ensures the user has admin role

Dependencies:
    - Flask-Login: User session management
    - Custom Logger: Application logging utility

Note:
    This module primarily exports decorators from the decorators submodule
    for convenient access throughout the application.
"""

import logging
from app.utils.decorators import (
    client_required,
    employee_required,
    admin_required
)

# Initialize logger
logger = logging.getLogger(__name__)

# Define public API
__all__ = [
    'client_required',
    'employee_required',
    'admin_required'
]

# Log module initialization
logger.debug("Utils module initialized with decorators: %s", __all__)
