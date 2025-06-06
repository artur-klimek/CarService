"""
Database Initialization Module for CarService Application.

This module provides functionality to initialize the database with test data
for development and testing purposes. It creates sample users, vehicles,
services, and service history entries to facilitate application testing.

Key Features:
    - Creates test users with different roles (client, employee, admin)
    - Initializes test vehicles with realistic data
    - Sets up sample services with various statuses
    - Creates service history entries for tracking
    - Handles database session management

Dependencies:
    - app: For application context and database access
    - app.models: For database model definitions
    - datetime: For date and time handling
    - werkzeug.security: For password hashing

Note:
    This module is intended for development and testing purposes only.
    It should not be used in production environments.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User, Vehicle, Service, ServiceHistory

# Initialize logger
logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Initialize the database with test data.

    This function creates a set of test data including:
    - Test users (client, employee, admin)
    - Test vehicles with realistic data
    - Sample services with various statuses
    - Service history entries

    The function operates within an application context to ensure
    proper database session management.

    Raises:
        SQLAlchemyError: If database operations fail
        Exception: For other unexpected errors during initialization

    Note:
        This function should only be used in development/testing environments.
        It will clear existing data if run multiple times.
    """
    logger.info("Starting database initialization")
    app = create_app()

    try:
        with app.app_context():
            logger.debug("Creating test users")
            # Create test users
            client = User(
                username='test_client',
                email='client@test.com',
                password_hash=generate_password_hash('test123'),
                first_name='Test',
                last_name='Client',
                role='client'
            )
            logger.debug(f"Created test client user: {client.username}")
            
            employee = User(
                username='test_employee',
                email='employee@test.com',
                password_hash=generate_password_hash('test123'),
                first_name='Test',
                last_name='Employee',
                role='employee'
            )
            logger.debug(f"Created test employee user: {employee.username}")
            
            admin = User(
                username='test_admin',
                email='admin@test.com',
                password_hash=generate_password_hash('test123'),
                first_name='Test',
                last_name='Admin',
                role='admin'
            )
            logger.debug(f"Created test admin user: {admin.username}")
            
            db.session.add_all([client, employee, admin])
            db.session.commit()
            logger.info("Test users created successfully")
            
            logger.debug("Creating test vehicles")
            # Create test vehicles
            vehicles: List[Vehicle] = [
                Vehicle(
                    make='Toyota',
                    model='Corolla',
                    year=2020,
                    license_plate='ABC123',
                    vin='1HGCM82633A123456',
                    owner_id=client.id
                ),
                Vehicle(
                    make='Honda',
                    model='Civic',
                    year=2021,
                    license_plate='XYZ789',
                    vin='2HGES16575H123456',
                    owner_id=client.id
                )
            ]
            
            db.session.add_all(vehicles)
            db.session.commit()
            logger.info(f"Created {len(vehicles)} test vehicles")
            
            logger.debug("Creating test services")
            # Create test services
            services: List[Service] = [
                Service(
                    vehicle_id=vehicles[0].id,
                    client_id=client.id,
                    description='Regular maintenance',
                    priority='medium',
                    status='pending',
                    preferred_date=datetime.now() + timedelta(days=7),
                    additional_notes='Oil change needed'
                ),
                Service(
                    vehicle_id=vehicles[1].id,
                    client_id=client.id,
                    description='Brake repair',
                    priority='high',
                    status='accepted',
                    preferred_date=datetime.now() + timedelta(days=3),
                    employee_id=employee.id,
                    scheduled_date=datetime.now() + timedelta(days=3),
                    diagnosis='Brake pads worn out',
                    service_plan='Replace brake pads and rotors',
                    estimated_cost=300.00,
                    estimated_duration=2
                )
            ]
            
            db.session.add_all(services)
            db.session.commit()
            logger.info(f"Created {len(services)} test services")
            
            logger.debug("Creating service history entries")
            # Add history entries
            for service in services:
                if service.status == 'pending':
                    logger.debug(
                        f"Adding history entry for pending service {service.id}"
                    )
                    service.add_history_entry('Service request created', client.id)
                else:
                    logger.debug(
                        f"Adding history entries for accepted service {service.id}"
                    )
                    service.add_history_entry('Service request created', client.id)
                    service.add_history_entry(
                        'Service accepted by employee',
                        employee.id
                    )
                    service.add_history_entry('Diagnosis completed', employee.id)
            
            db.session.commit()
            logger.info("Service history entries created successfully")
            
            logger.info("Database initialization completed successfully")
            print("Test data initialized successfully!")

    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        db.session.rollback()
        raise


if __name__ == '__main__':
    # Configure logging for script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    init_db()
