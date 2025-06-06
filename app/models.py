"""
Database Models Module for CarService Application.

This module defines the core database models used in the CarService application.
It includes models for users, vehicles, services, and service history, along with
their relationships and business logic.

Key Models:
    - User: Handles user authentication, roles, and permissions
    - Vehicle: Manages vehicle information and ownership
    - Service: Handles service requests, status management, and workflow
    - ServiceHistory: Tracks service status changes and updates

Features:
    - Role-based access control
    - Service status workflow management
    - Vehicle ownership tracking
    - Service history logging
    - User authentication and authorization

Dependencies:
    - flask_login: For user authentication
    - werkzeug.security: For password hashing
    - app: For database and login manager access

Note:
    All models include proper relationships, constraints, and business logic
    validation to ensure data integrity and application security.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

# Initialize logger
logger = logging.getLogger(__name__)


class User(UserMixin, db.Model):
    """
    User model for authentication and user management.

    This model handles user authentication, role management, and user-related
    operations. It implements the UserMixin for Flask-Login integration.

    Attributes:
        id (int): Primary key
        username (str): Unique username
        email (str): Unique email address
        password_hash (str): Hashed password
        role (str): User role (client, employee, admin)
        first_name (str): User's first name
        last_name (str): User's last name
        phone (str): User's phone number
        address (str): User's address
        created_at (datetime): Account creation timestamp
        updated_at (datetime): Last update timestamp
        last_login (datetime): Last login timestamp
        is_active (bool): Account status

    Relationships:
        vehicles: One-to-many relationship with Vehicle model
        client_services: Services where user is the client
        employee_services: Services where user is the employee

    Methods:
        set_password: Securely set user password
        check_password: Verify password
        is_admin/employee/client: Role checks
        get_full_name: Get user's full name
        can_manage_users/vehicles: Permission checks
        can_modify/delete_user: User management permissions
        can_change_role: Role management permission
        get_vehicles: Get user's vehicles
        can_add_vehicle: Check vehicle limit
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='client')
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    vehicles = db.relationship(
        'Vehicle',
        back_populates='owner',
        lazy='dynamic'
    )
    client_services = db.relationship(
        'Service',
        foreign_keys='Service.client_id',
        back_populates='client'
    )
    employee_services = db.relationship(
        'Service',
        foreign_keys='Service.employee_id',
        back_populates='employee'
    )
    
    def __init__(self, username: str, email: str, role: str = 'client') -> None:
        """
        Initialize a new user.

        Args:
            username (str): User's username
            email (str): User's email address
            role (str, optional): User's role. Defaults to 'client'.

        Note:
            Password must be set separately using set_password method.
        """
        self.username = username
        self.email = email
        self.role = role
        logger.debug(f"Initialized new user: {username} with role: {role}")
    
    def set_password(self, password: str) -> None:
        """
        Set user's password securely.

        Args:
            password (str): Plain text password to hash and store

        Note:
            Uses werkzeug's generate_password_hash for secure hashing.
        """
        self.password_hash = generate_password_hash(password)
        logger.debug(f"Password set for user: {self.username}")
    
    def check_password(self, password: str) -> bool:
        """
        Verify user's password.

        Args:
            password (str): Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        is_valid = check_password_hash(self.password_hash, password)
        logger.debug(f"Password check for user {self.username}: {is_valid}")
        return is_valid
    
    def is_admin(self) -> bool:
        """
        Check if user is an administrator.

        Returns:
            bool: True if user is an admin, False otherwise
        """
        return self.role == 'admin'
    
    def is_employee(self) -> bool:
        """
        Check if user is an employee.

        Returns:
            bool: True if user is an employee, False otherwise
        """
        return self.role == 'employee'
    
    def is_client(self) -> bool:
        """
        Check if user is a client.

        Returns:
            bool: True if user is a client, False otherwise
        """
        return self.role == 'client'
    
    def get_full_name(self) -> str:
        """
        Get user's full name.

        Returns:
            str: User's full name if available, otherwise username
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def can_manage_users(self) -> bool:
        """
        Check if user can manage other users.

        Returns:
            bool: True if user is admin or employee, False otherwise
        """
        return self.is_admin() or self.is_employee()
    
    def can_manage_vehicles(self) -> bool:
        """
        Check if user can manage vehicles.

        Returns:
            bool: True if user is admin or employee, False otherwise
        """
        return self.is_admin() or self.is_employee()
    
    def can_modify_user(self, target_user: 'User') -> bool:
        """
        Check if user can modify another user's data.

        Args:
            target_user (User): The user to be modified

        Returns:
            bool: True if user has permission to modify target_user
        """
        can_modify = self.is_admin() or (
            self.is_employee() and target_user.is_client()
        )
        logger.debug(
            f"User {self.username} can modify {target_user.username}: {can_modify}"
        )
        return can_modify
    
    def can_delete_user(self, target_user: 'User') -> bool:
        """
        Check if user can delete another user.

        Args:
            target_user (User): The user to be deleted

        Returns:
            bool: True if user is admin, False otherwise
        """
        can_delete = self.is_admin()
        logger.debug(
            f"User {self.username} can delete {target_user.username}: {can_delete}"
        )
        return can_delete
    
    def can_change_role(self) -> bool:
        """
        Check if user can change other users' roles.

        Returns:
            bool: True if user is admin, False otherwise
        """
        return self.is_admin()
    
    def get_vehicles(self) -> List['Vehicle']:
        """
        Get all vehicles owned by the user.

        Returns:
            List[Vehicle]: List of vehicles owned by the user
        """
        return self.vehicles.all()
    
    def can_add_vehicle(self) -> bool:
        """
        Check if user can add more vehicles.

        Returns:
            bool: True if user hasn't reached vehicle limit, False otherwise
        """
        from app.config import Config
        config = Config()
        can_add = len(self.vehicles.all()) < config.get_max_vehicles_per_user()
        logger.debug(f"User {self.username} can add vehicle: {can_add}")
        return can_add
    
    def __repr__(self) -> str:
        """
        Get string representation of the user.

        Returns:
            str: String representation of the user
        """
        return f'<User {self.username}>'


class Vehicle(db.Model):
    """
    Vehicle model for storing vehicle information.

    This model manages vehicle data and ownership information.

    Attributes:
        id (int): Primary key
        owner_id (int): Foreign key to User model
        make (str): Vehicle make
        model (str): Vehicle model
        year (int): Vehicle year
        vin (str): Vehicle identification number
        license_plate (str): Vehicle license plate
        color (str): Vehicle color
        mileage (int): Vehicle mileage
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp

    Relationships:
        owner: Many-to-one relationship with User model
        services: One-to-many relationship with Service model
    """
    
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(17), unique=True, nullable=False)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    color = db.Column(db.String(30))
    mileage = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    owner = db.relationship('User', back_populates='vehicles')
    services = db.relationship(
        'Service',
        back_populates='vehicle',
        lazy='dynamic'
    )
    
    def __init__(
        self,
        owner_id: int,
        make: str,
        model: str,
        year: int,
        vin: str,
        license_plate: str,
        color: Optional[str] = None,
        mileage: Optional[int] = None
    ) -> None:
        """
        Initialize a new vehicle.

        Args:
            owner_id (int): ID of the vehicle owner
            make (str): Vehicle make
            model (str): Vehicle model
            year (int): Vehicle year
            vin (str): Vehicle identification number
            license_plate (str): Vehicle license plate
            color (Optional[str]): Vehicle color
            mileage (Optional[int]): Vehicle mileage

        Note:
            VIN and license plate must be unique.
        """
        self.owner_id = owner_id
        self.make = make
        self.model = model
        self.year = year
        self.vin = vin
        self.license_plate = license_plate
        self.color = color
        self.mileage = mileage
        logger.debug(
            f"Initialized new vehicle: {make} {model} ({license_plate})"
        )
    
    def __repr__(self) -> str:
        """
        Get string representation of the vehicle.

        Returns:
            str: String representation of the vehicle
        """
        return f'<Vehicle {self.make} {self.model} ({self.license_plate})>'


class Service(db.Model):
    """
    Service model for managing service requests and workflow.

    This model handles the complete service lifecycle, from initial request
    to completion, including status management, employee assignment, and
    cost tracking.

    Attributes:
        id (int): Primary key
        vehicle_id (int): Foreign key to Vehicle model
        client_id (int): Foreign key to User model (client)
        employee_id (int): Foreign key to User model (employee)
        description (str): Service description
        priority (str): Service priority level
        status (str): Current service status
        preferred_date (datetime): Client's preferred date
        scheduled_date (datetime): Scheduled service date
        diagnosis (str): Service diagnosis
        service_plan (str): Service plan
        estimated_cost (float): Estimated service cost
        actual_cost (float): Actual service cost
        parts_needed (str): Required parts
        notes (str): Additional notes
        additional_notes (str): Client's additional notes
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp

    Relationships:
        vehicle: Many-to-one relationship with Vehicle model
        client: Many-to-one relationship with User model
        employee: Many-to-one relationship with User model
        history: One-to-many relationship with ServiceHistory model

    Constants:
        STATUS_*: Service status constants
        STATUS_COLORS: Bootstrap color classes for statuses
        PRIORITY_COLORS: Bootstrap color classes for priorities
        STATUS_TRANSITIONS: Valid status transitions
        CLIENT_CANCELLABLE_STATES: States where client can cancel
        CLIENT_DATE_CHANGE_STATES: States where client can change date
        EMPLOYEE_DATE_PROPOSAL_STATES: States where employee can propose date
        EMPLOYEE_REQUIRED_STATES: States requiring employee assignment
        UPDATABLE_STATES: States that can be updated

    Methods:
        assign_employee: Assign or change service employee
        can_transition_to: Check valid status transition
        can_client_cancel: Check if client can cancel
        can_client_request_date_change: Check if client can change date
        can_employee_propose_date: Check if employee can propose date
        requires_employee: Check if employee required
        can_be_updated: Check if service can be updated
        validate_costs: Validate cost fields
        add_history_entry: Add service history entry
        update_status: Update service status
        request_date_change: Request date change
        confirm_date: Confirm scheduled date
        reject_date: Reject scheduled date
        cancel: Cancel service
    """
    
    __tablename__ = 'services'
    
    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_CLIENT_CONFIRMED = 'client_confirmed'
    STATUS_WAITING_FOR_VEHICLE = 'waiting_for_vehicle'
    STATUS_VEHICLE_RECEIVED = 'vehicle_received'
    STATUS_DIAGNOSIS_PENDING = 'diagnosis_pending'
    STATUS_DIAGNOSIS_COMPLETED = 'diagnosis_completed'
    STATUS_CLIENT_CONSULTATION = 'client_consultation'
    STATUS_CLIENT_APPROVED = 'client_approved'
    STATUS_WAITING_FOR_PARTS = 'waiting_for_parts'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_READY_FOR_PAYMENT = 'ready_for_payment'
    STATUS_PAYMENT_RECEIVED = 'payment_received'
    STATUS_READY_FOR_PICKUP = 'ready_for_pickup'
    STATUS_FINISHED = 'finished'
    STATUS_CANCELLED = 'cancelled'

    # Status colors for UI
    STATUS_COLORS: Dict[str, str] = {
        STATUS_PENDING: 'warning',
        STATUS_ACCEPTED: 'info',
        STATUS_SCHEDULED: 'info',
        STATUS_CLIENT_CONFIRMED: 'info',
        STATUS_WAITING_FOR_VEHICLE: 'warning',
        STATUS_VEHICLE_RECEIVED: 'info',
        STATUS_DIAGNOSIS_PENDING: 'warning',
        STATUS_DIAGNOSIS_COMPLETED: 'info',
        STATUS_CLIENT_CONSULTATION: 'warning',
        STATUS_CLIENT_APPROVED: 'info',
        STATUS_WAITING_FOR_PARTS: 'warning',
        STATUS_IN_PROGRESS: 'primary',
        STATUS_COMPLETED: 'success',
        STATUS_READY_FOR_PAYMENT: 'warning',
        STATUS_PAYMENT_RECEIVED: 'success',
        STATUS_READY_FOR_PICKUP: 'success',
        STATUS_FINISHED: 'success',
        STATUS_CANCELLED: 'danger'
    }

    # Priority colors for UI
    PRIORITY_COLORS: Dict[str, str] = {
        'low': 'success',
        'normal': 'info',
        'high': 'danger'
    }

    # Valid status transitions
    STATUS_TRANSITIONS: Dict[str, List[str]] = {
        STATUS_PENDING: [STATUS_ACCEPTED, STATUS_CANCELLED],
        STATUS_ACCEPTED: [
            STATUS_SCHEDULED,
            STATUS_CANCELLED,
            STATUS_WAITING_FOR_VEHICLE
        ],
        STATUS_SCHEDULED: [
            STATUS_CLIENT_CONFIRMED,
            STATUS_PENDING,
            STATUS_CANCELLED
        ],
        STATUS_CLIENT_CONFIRMED: [
            STATUS_WAITING_FOR_VEHICLE,
            STATUS_CANCELLED
        ],
        STATUS_WAITING_FOR_VEHICLE: [
            STATUS_VEHICLE_RECEIVED,
            STATUS_CANCELLED
        ],
        STATUS_VEHICLE_RECEIVED: [
            STATUS_DIAGNOSIS_PENDING,
            STATUS_CANCELLED
        ],
        STATUS_DIAGNOSIS_PENDING: [
            STATUS_DIAGNOSIS_COMPLETED,
            STATUS_CANCELLED
        ],
        STATUS_DIAGNOSIS_COMPLETED: [
            STATUS_CLIENT_APPROVED,
            STATUS_CLIENT_CONSULTATION,
            STATUS_CANCELLED
        ],
        STATUS_CLIENT_CONSULTATION: [
            STATUS_DIAGNOSIS_COMPLETED,
            STATUS_CANCELLED
        ],
        STATUS_CLIENT_APPROVED: [
            STATUS_WAITING_FOR_PARTS,
            STATUS_IN_PROGRESS,
            STATUS_CANCELLED
        ],
        STATUS_WAITING_FOR_PARTS: [
            STATUS_IN_PROGRESS,
            STATUS_CANCELLED
        ],
        STATUS_IN_PROGRESS: [
            STATUS_COMPLETED,
            STATUS_CANCELLED
        ],
        STATUS_COMPLETED: [
            STATUS_READY_FOR_PAYMENT,
            STATUS_CANCELLED
        ],
        STATUS_READY_FOR_PAYMENT: [
            STATUS_PAYMENT_RECEIVED,
            STATUS_CANCELLED
        ],
        STATUS_PAYMENT_RECEIVED: [
            STATUS_READY_FOR_PICKUP,
            STATUS_IN_PROGRESS,
            STATUS_CANCELLED
        ],
        STATUS_READY_FOR_PICKUP: [
            STATUS_FINISHED,
            STATUS_CANCELLED
        ],
        STATUS_FINISHED: [],  # Terminal state
        STATUS_CANCELLED: []  # Terminal state
    }

    # Client can only cancel in these states
    CLIENT_CANCELLABLE_STATES: List[str] = [
        STATUS_PENDING,
        STATUS_SCHEDULED,
        STATUS_CLIENT_CONFIRMED
    ]

    # Client can request date change in these states
    CLIENT_DATE_CHANGE_STATES: List[str] = [
        STATUS_SCHEDULED,
        STATUS_CLIENT_CONFIRMED
    ]

    # Employee can propose date in these states
    EMPLOYEE_DATE_PROPOSAL_STATES: List[str] = [
        STATUS_PENDING,
        STATUS_ACCEPTED
    ]

    # States that require employee assignment
    EMPLOYEE_REQUIRED_STATES: List[str] = [
        STATUS_ACCEPTED,
        STATUS_SCHEDULED,
        STATUS_CLIENT_CONFIRMED,
        STATUS_WAITING_FOR_VEHICLE,
        STATUS_VEHICLE_RECEIVED,
        STATUS_DIAGNOSIS_PENDING,
        STATUS_DIAGNOSIS_COMPLETED,
        STATUS_CLIENT_CONSULTATION,
        STATUS_CLIENT_APPROVED,
        STATUS_WAITING_FOR_PARTS,
        STATUS_IN_PROGRESS,
        STATUS_COMPLETED,
        STATUS_READY_FOR_PAYMENT,
        STATUS_PAYMENT_RECEIVED,
        STATUS_READY_FOR_PICKUP,
        STATUS_FINISHED
    ]

    # States that can be updated
    UPDATABLE_STATES: List[str] = [
        STATUS_ACCEPTED,
        STATUS_SCHEDULED,
        STATUS_CLIENT_CONFIRMED,
        STATUS_WAITING_FOR_VEHICLE,
        STATUS_VEHICLE_RECEIVED,
        STATUS_DIAGNOSIS_PENDING,
        STATUS_DIAGNOSIS_COMPLETED,
        STATUS_CLIENT_CONSULTATION,
        STATUS_CLIENT_APPROVED,
        STATUS_WAITING_FOR_PARTS,
        STATUS_IN_PROGRESS,
        STATUS_COMPLETED,
        STATUS_READY_FOR_PAYMENT,
        STATUS_PAYMENT_RECEIVED,
        STATUS_READY_FOR_PICKUP
    ]

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey('vehicles.id'),
        nullable=False
    )
    client_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True
    )
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='normal')
    status = db.Column(
        db.String(50),
        nullable=False,
        default=STATUS_PENDING
    )
    preferred_date = db.Column(db.DateTime, nullable=True)
    scheduled_date = db.Column(db.DateTime, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    service_plan = db.Column(db.Text, nullable=True)
    estimated_cost = db.Column(db.Float, nullable=True)
    actual_cost = db.Column(db.Float, nullable=True)
    parts_needed = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    additional_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    vehicle = db.relationship('Vehicle', back_populates='services')
    client = db.relationship(
        'User',
        foreign_keys=[client_id],
        back_populates='client_services'
    )
    employee = db.relationship(
        'User',
        foreign_keys=[employee_id],
        back_populates='employee_services'
    )
    history = db.relationship(
        'ServiceHistory',
        back_populates='service',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def assign_employee(self, employee_id: int, user_id: int) -> None:
        """
        Assign or change employee for the service.

        Args:
            employee_id (int): ID of the employee to assign
            user_id (int): ID of the user making the assignment

        Note:
            If service is pending, it will be automatically accepted.
            History entry will be created for the assignment.
        """
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_ACCEPTED
            self.add_history_entry(
                f'Service assigned to {User.query.get(employee_id).get_full_name()}',
                user_id
            )
            logger.info(
                f"Service {self.id} assigned to employee {employee_id} "
                f"and status changed to accepted"
            )
        else:
            old_employee = self.employee.get_full_name() if self.employee else 'None'
            new_employee = User.query.get(employee_id).get_full_name()
            self.add_history_entry(
                f'Service reassigned from {old_employee} to {new_employee}',
                user_id
            )
            logger.info(
                f"Service {self.id} reassigned from {old_employee} "
                f"to {new_employee}"
            )
        
        self.employee_id = employee_id
        db.session.commit()

    def can_transition_to(self, new_status: str) -> bool:
        """
        Check if transition to new status is valid.

        Args:
            new_status (str): The status to transition to

        Returns:
            bool: True if transition is valid, False otherwise

        Note:
            Also checks if employee assignment is required for the new status.
        """
        # Check if the transition is allowed
        if new_status not in self.STATUS_TRANSITIONS.get(self.status, []):
            logger.warning(
                f"Invalid status transition from {self.status} to {new_status}"
            )
            return False
        
        # Check if the new status requires employee assignment
        if new_status in self.EMPLOYEE_REQUIRED_STATES and not self.employee_id:
            logger.warning(
                f"Cannot transition to {new_status} without assigned employee"
            )
            return False
        
        logger.debug(
            f"Valid status transition from {self.status} to {new_status}"
        )
        return True
    
    def can_client_cancel(self) -> bool:
        """
        Check if client can cancel the service.

        Returns:
            bool: True if client can cancel in current status
        """
        can_cancel = self.status in self.CLIENT_CANCELLABLE_STATES
        logger.debug(f"Client can cancel service {self.id}: {can_cancel}")
        return can_cancel
    
    def can_client_request_date_change(self) -> bool:
        """
        Check if client can request a date change.

        Returns:
            bool: True if client can request date change in current status
        """
        can_change = self.status in self.CLIENT_DATE_CHANGE_STATES
        logger.debug(
            f"Client can request date change for service {self.id}: {can_change}"
        )
        return can_change
    
    def can_employee_propose_date(self) -> bool:
        """
        Check if employee can propose a date.

        Returns:
            bool: True if employee can propose date in current status
        """
        can_propose = self.status in self.EMPLOYEE_DATE_PROPOSAL_STATES
        logger.debug(
            f"Employee can propose date for service {self.id}: {can_propose}"
        )
        return can_propose
    
    def requires_employee(self) -> bool:
        """
        Check if current status requires employee assignment.

        Returns:
            bool: True if current status requires employee
        """
        requires = self.status in self.EMPLOYEE_REQUIRED_STATES
        logger.debug(
            f"Service {self.id} requires employee in current status: {requires}"
        )
        return requires
    
    def can_be_updated(self) -> bool:
        """
        Check if service can be updated in current status.

        Returns:
            bool: True if service can be updated
        """
        can_update = self.status in self.UPDATABLE_STATES
        logger.debug(f"Service {self.id} can be updated: {can_update}")
        return can_update
    
    def validate_costs(
        self,
        estimated_cost: Optional[float] = None,
        actual_cost: Optional[float] = None
    ) -> None:
        """
        Validate cost fields.

        Args:
            estimated_cost (Optional[float]): Estimated cost to validate
            actual_cost (Optional[float]): Actual cost to validate

        Raises:
            ValueError: If cost values are invalid
        """
        if estimated_cost is not None:
            try:
                if estimated_cost:
                    self.estimated_cost = float(estimated_cost)
                else:
                    self.estimated_cost = None
                logger.debug(
                    f"Updated estimated cost for service {self.id}: "
                    f"{self.estimated_cost}"
                )
            except ValueError:
                logger.error(
                    f"Invalid estimated cost value: {estimated_cost}"
                )
                raise ValueError("Estimated cost must be a valid number")
        
        if actual_cost is not None:
            try:
                if actual_cost:
                    self.actual_cost = float(actual_cost)
                else:
                    self.actual_cost = None
                logger.debug(
                    f"Updated actual cost for service {self.id}: "
                    f"{self.actual_cost}"
                )
            except ValueError:
                logger.error(f"Invalid actual cost value: {actual_cost}")
                raise ValueError("Actual cost must be a valid number")
    
    def add_history_entry(self, description: str, user_id: int) -> None:
        """
        Add a history entry for the service.

        Args:
            description (str): Description of the history entry
            user_id (int): ID of the user creating the entry
        """
        history_entry = ServiceHistory(
            service_id=self.id,
            user_id=user_id,
            description=description
        )
        db.session.add(history_entry)
        self.history.append(history_entry)
        logger.debug(
            f"Added history entry for service {self.id}: {description}"
        )
    
    def update_status(
        self,
        new_status: str,
        user_id: int,
        additional_info: Optional[str] = None
    ) -> None:
        """
        Update service status with history entry.

        Args:
            new_status (str): New status to set
            user_id (int): ID of the user updating status
            additional_info (Optional[str]): Additional information for history

        Raises:
            ValueError: If status transition is invalid
        """
        if not self.can_transition_to(new_status):
            if new_status in self.EMPLOYEE_REQUIRED_STATES and not self.employee_id:
                error_msg = "Cannot transition to this status without assigned employee"
                logger.error(error_msg)
                raise ValueError(error_msg)
            error_msg = f"Invalid status transition from {self.status} to {new_status}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        old_status = self.status
        self.status = new_status
        
        # Create history entry
        description = f"Status changed from {old_status} to {new_status}"
        if additional_info:
            description += f": {additional_info}"
        
        self.add_history_entry(description, user_id)
        logger.info(
            f"Service {self.id} status updated from {old_status} to {new_status}"
        )
        db.session.commit()
    
    def request_date_change(
        self,
        new_date: datetime,
        user_id: int,
        is_client_request: bool = False
    ) -> None:
        """
        Request a date change for the service.

        Args:
            new_date (datetime): New requested date
            user_id (int): ID of the user requesting change
            is_client_request (bool): Whether request is from client

        Raises:
            ValueError: If date change is not allowed
        """
        if is_client_request and self.status not in [
            self.STATUS_PENDING,
            self.STATUS_ACCEPTED,
            self.STATUS_SCHEDULED
        ]:
            error_msg = (
                "Client can only request date changes for pending or "
                "scheduled services"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.preferred_date = new_date
        if is_client_request:
            self.status = self.STATUS_PENDING
            self.add_history_entry(
                f"Client requested date change to {new_date.strftime('%Y-%m-%d')}",
                user_id
            )
            logger.info(
                f"Client requested date change for service {self.id} "
                f"to {new_date.strftime('%Y-%m-%d')}"
            )
        else:
            self.status = self.STATUS_SCHEDULED
            self.scheduled_date = new_date
            self.add_history_entry(
                f"Employee proposed new date: {new_date.strftime('%Y-%m-%d')}",
                user_id
            )
            logger.info(
                f"Employee proposed new date for service {self.id}: "
                f"{new_date.strftime('%Y-%m-%d')}"
            )
        
        db.session.commit()
    
    def confirm_date(self, user_id: int) -> None:
        """
        Confirm the scheduled date.

        Args:
            user_id (int): ID of the user confirming date

        Raises:
            ValueError: If date cannot be confirmed
        """
        if self.status != self.STATUS_SCHEDULED:
            error_msg = "Can only confirm dates for scheduled services"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not self.employee_id:
            error_msg = "Cannot confirm date without assigned employee"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.status = self.STATUS_CLIENT_CONFIRMED
        self.add_history_entry("Client confirmed the scheduled date", user_id)
        logger.info(f"Client confirmed date for service {self.id}")
        db.session.commit()
    
    def reject_date(self, user_id: int, reason: Optional[str] = None) -> None:
        """
        Reject the scheduled date.

        Args:
            user_id (int): ID of the user rejecting date
            reason (Optional[str]): Reason for rejection

        Raises:
            ValueError: If date cannot be rejected
        """
        if self.status != self.STATUS_SCHEDULED:
            error_msg = "Can only reject dates for scheduled services"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.status = self.STATUS_PENDING
        description = "Client rejected the scheduled date"
        if reason:
            description += f": {reason}"
        
        self.add_history_entry(description, user_id)
        logger.info(f"Client rejected date for service {self.id}")
        db.session.commit()
    
    def cancel(self, user_id: int, reason: Optional[str] = None) -> None:
        """
        Cancel the service.

        Args:
            user_id (int): ID of the user cancelling service
            reason (Optional[str]): Reason for cancellation

        Raises:
            ValueError: If service cannot be cancelled
        """
        if not self.can_transition_to(self.STATUS_CANCELLED):
            error_msg = "Service cannot be cancelled in its current state"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.status = self.STATUS_CANCELLED
        description = "Service cancelled"
        if reason:
            description += f": {reason}"
        
        self.add_history_entry(description, user_id)
        logger.info(f"Service {self.id} cancelled")
        db.session.commit()
    
    @property
    def status_color(self) -> str:
        """
        Get the Bootstrap color class for the current status.

        Returns:
            str: Bootstrap color class name
        """
        return self.STATUS_COLORS.get(self.status, 'secondary')
    
    @property
    def priority_color(self) -> str:
        """
        Get the Bootstrap color class for the current priority.

        Returns:
            str: Bootstrap color class name
        """
        return self.PRIORITY_COLORS.get(self.priority, 'secondary')
    
    def __repr__(self) -> str:
        """
        Get string representation of the service.

        Returns:
            str: String representation of the service
        """
        return f'<Service {self.id} - {self.status}>'


class ServiceHistory(db.Model):
    """
    Service history model for tracking service changes.

    This model maintains a history of all changes and updates to services,
    including status changes, employee assignments, and other modifications.

    Attributes:
        id (int): Primary key
        service_id (int): Foreign key to Service model
        user_id (int): Foreign key to User model
        description (str): Description of the history entry
        created_at (datetime): Creation timestamp

    Relationships:
        service: Many-to-one relationship with Service model
        user: Many-to-one relationship with User model
    """
    
    __tablename__ = 'service_history'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(
        db.Integer,
        db.ForeignKey('services.id'),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relationships
    service = db.relationship('Service', back_populates='history')
    user = db.relationship('User', backref='service_history_entries')
    
    def __repr__(self) -> str:
        """
        Get string representation of the service history entry.

        Returns:
            str: String representation of the history entry
        """
        return f'<ServiceHistory {self.id} - {self.service_id}>'


@login_manager.user_loader
def load_user(id: str) -> Optional[User]:
    """
    Load user by ID for Flask-Login.

    Args:
        id (str): User ID to load

    Returns:
        Optional[User]: User object if found, None otherwise
    """
    user = User.query.get(int(id))
    logger.debug(f"Loading user by ID {id}: {user is not None}")
    return user
