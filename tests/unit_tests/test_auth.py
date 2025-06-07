"""Test suite for authentication functionality.

This module contains tests for user authentication, including:
- User model functionality
- Login form validation
- Registration form validation
- Authentication endpoints
- Protected routes
- Session management
"""

import unittest
from flask import url_for, session, current_app
from app import create_app, db
from app.models import User
from app.config import Config
from app.forms import LoginForm, RegistrationForm
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
class TestConfig(Config):
    """Test configuration class.
    
    This class provides test-specific configuration settings.
    It inherits from the base Config class and overrides necessary settings
    for testing environment.
    """
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    SERVER_NAME = 'localhost'
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'
    DEFAULT_ADMIN = {
        'username': 'testadmin',
        'email': 'testadmin@example.com',
        'password': 'testpass123',
        'role': 'admin'
    }
    DEFAULT_CLIENT = {
        'username': 'testclient',
        'email': 'testclient@example.com',
        'password': 'testpass123',
        'role': 'client'
    }
    DEFAULT_EMPLOYEE = {
        'username': 'testemployee',
        'email': 'testemployee@example.com',
        'password': 'testpass123',
        'role': 'employee'
    }

class AuthTestCase(unittest.TestCase):
    """Test case for authentication functionality.
    
    This class contains test methods for all authentication-related features:
    - User model tests
    - Form validation tests
    - Endpoint tests
    - Session management tests
    """
    
    def setUp(self):
        """Set up test environment."""
        logger.info("Setting up test environment")
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            role='client'
        )
        self.test_user.set_password('testpass123')
        db.session.add(self.test_user)
        db.session.commit()
        logger.info("Test environment setup complete")

    def tearDown(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment")
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()
        logger.info("Test environment cleanup complete")

    def test_user_model(self):
        """Test User model authentication methods."""
        # Test password setting and checking
        self.assertTrue(self.test_user.check_password('testpass123'))
        self.assertFalse(self.test_user.check_password('wrongpass'))
        
        # Test role checking
        self.assertTrue(self.test_user.is_client())
        self.assertFalse(self.test_user.is_admin())
        self.assertFalse(self.test_user.is_employee())

    def test_login_form(self):
        """Test login form validation."""
        with self.app.test_request_context():
            # Test valid form
            form = LoginForm(
                username='testuser',
                password='testpass123',
                remember_me=True,
                meta={'csrf': False}  # Disable CSRF for testing
            )
            self.assertTrue(form.validate())
            
            # Test invalid username
            form = LoginForm(
                username='wronguser',
                password='testpass123',
                remember_me=True,
                meta={'csrf': False}
            )
            self.assertFalse(form.validate())
            
            # Test invalid password
            form = LoginForm(
                username='testuser',
                password='wrongpass',
                remember_me=True,
                meta={'csrf': False}
            )
            self.assertFalse(form.validate())

    def test_registration_form(self):
        """Test registration form validation."""
        with self.app.test_request_context():
            # Test valid form
            form = RegistrationForm(
                username='newuser',
                email='new@example.com',
                password='newpass123',
                password2='newpass123',
                meta={'csrf': False}
            )
            self.assertTrue(form.validate())
            
            # Test password mismatch
            form = RegistrationForm(
                username='newuser',
                email='new@example.com',
                password='newpass123',
                password2='differentpass',
                meta={'csrf': False}
            )
            self.assertFalse(form.validate())
            
            # Test existing username
            form = RegistrationForm(
                username='testuser',  # already exists
                email='new@example.com',
                password='newpass123',
                password2='newpass123',
                meta={'csrf': False}
            )
            self.assertFalse(form.validate())

    def test_login_endpoint(self):
        """Test login endpoint functionality."""
        with self.app.test_client() as client:
            # Test successful login
            response = client.post(
                '/auth/login',
                data={
                    'username': 'testuser',
                    'password': 'testpass123',
                    'remember_me': True
                },
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Welcome', response.data)
            
            # Test failed login
            response = client.post(
                '/auth/login',
                data={
                    'username': 'testuser',
                    'password': 'wrongpass',
                    'remember_me': True
                },
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Invalid username or password', response.data)

    def test_registration_endpoint(self):
        """Test registration endpoint functionality."""
        with self.app.test_client() as client:
            # Test successful registration
            response = client.post(
                '/auth/register',
                data={
                    'username': 'newuser',
                    'email': 'new@example.com',
                    'password': 'newpass123',
                    'password2': 'newpass123'
                },
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Congratulations', response.data)
            
            # Test registration with existing username
            response = client.post(
                '/auth/register',
                data={
                    'username': 'testuser',  # already exists
                    'email': 'another@example.com',
                    'password': 'newpass123',
                    'password2': 'newpass123'
                },
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Please use a different username', response.data)

    def test_logout(self):
        """Test logout functionality."""
        with self.app.test_client() as client:
            # Login first
            client.post(
                '/auth/login',
                data={
                    'username': 'testuser',
                    'password': 'testpass123',
                    'remember_me': True
                }
            )
            
            # Test logout
            response = client.get('/auth/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('user_id', session)

    def test_protected_routes(self):
        """Test access to protected routes."""
        with self.app.test_client() as client:
            # Try accessing protected route without login
            response = client.get('/user/profile', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Please log in to access this page', response.data)
            
            # Login and try again
            client.post(
                '/auth/login',
                data={
                    'username': 'testuser',
                    'password': 'testpass123',
                    'remember_me': True
                }
            )
            response = client.get('/user/profile', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'testuser', response.data)


if __name__ == '__main__':
    unittest.main() 