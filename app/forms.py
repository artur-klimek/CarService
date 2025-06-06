"""
Forms Module for CarService Application.

This module defines all form classes used in the CarService application.
It handles form validation, data processing, and user input management
for various application features.

Key Features:
    - User authentication forms (login, registration)
    - User profile management forms
    - Vehicle management forms
    - Service request and management forms
    - Contact and support forms
    - Search and filtering forms

Dependencies:
    - flask_wtf: For form handling and CSRF protection
    - wtforms: For form field definitions and validation
    - app.models: For database model integration
    - app: For database access

Note:
    All forms include proper validation and error handling.
    Custom validators ensure data integrity and business logic compliance.
"""

import logging
from datetime import datetime
from typing import Optional, Any, List, Tuple

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, PasswordField, SubmitField,
    SelectField, IntegerField, BooleanField, FloatField,
    DateField, DateTimeField, EmailField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, ValidationError,
    Optional, NumberRange, Regexp
)

from app.models import User, Vehicle
from app import db

# Initialize logger
logger = logging.getLogger(__name__)


class ContactForm(FlaskForm):
    """
    Contact form for sending messages to support.

    This form allows users to send messages to the support team.
    It includes fields for name, email, subject, and message content.

    Fields:
        name (StringField): User's full name
        email (StringField): User's email address
        subject (StringField): Message subject
        message (TextAreaField): Message content
        submit (SubmitField): Form submission button

    Validators:
        - All fields are required
        - Email must be valid
        - Name and subject have length restrictions
        - Message has minimum and maximum length requirements
    """
    name = StringField(
        'Name',
        validators=[
            DataRequired(),
            Length(min=2, max=50)
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email()
        ]
    )
    subject = StringField(
        'Subject',
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )
    message = TextAreaField(
        'Message',
        validators=[
            DataRequired(),
            Length(min=10, max=1000)
        ]
    )
    submit = SubmitField('Send Message')


class LoginForm(FlaskForm):
    """
    Form for user login.

    This form handles user authentication, including username,
    password, and remember me functionality.

    Fields:
        username (StringField): User's username
        password (PasswordField): User's password
        remember_me (BooleanField): Remember me checkbox
        submit (SubmitField): Form submission button

    Validators:
        - Username and password are required
    """
    username = StringField(
        'Username',
        validators=[DataRequired()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """
    Form for user registration.

    This form handles new user registration, including username,
    email, and password with confirmation.

    Fields:
        username (StringField): Desired username
        email (StringField): User's email address
        password (PasswordField): User's password
        password2 (PasswordField): Password confirmation
        submit (SubmitField): Form submission button

    Validators:
        - All fields are required
        - Username must be unique and 3-64 characters
        - Email must be valid and unique
        - Password must be at least 8 characters
        - Passwords must match

    Methods:
        validate_username: Ensures username uniqueness
        validate_email: Ensures email uniqueness
    """
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(
                min=3,
                max=64,
                message='Username must be between 3 and 64 characters long'
            )
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must be less than 120 characters')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters long')
        ]
    )
    password2 = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )
    submit = SubmitField('Register')
    
    def validate_username(self, username: StringField) -> None:
        """
        Validate username uniqueness.

        Args:
            username (StringField): The username field to validate

        Raises:
            ValidationError: If username is already taken
        """
        logger.debug(f"Validating username: {username.data}")
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            logger.warning(f"Username already taken: {username.data}")
            raise ValidationError('Please use a different username.')
        logger.debug(f"Username validation successful: {username.data}")
    
    def validate_email(self, email: StringField) -> None:
        """
        Validate email uniqueness.

        Args:
            email (StringField): The email field to validate

        Raises:
            ValidationError: If email is already registered
        """
        logger.debug(f"Validating email: {email.data}")
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            logger.warning(f"Email already registered: {email.data}")
            raise ValidationError('Please use a different email address.')
        logger.debug(f"Email validation successful: {email.data}")


class UserProfileForm(FlaskForm):
    """
    Form for user profile management.

    This form allows users to update their profile information,
    including personal details and contact information.

    Fields:
        first_name (StringField): User's first name
        last_name (StringField): User's last name
        email (StringField): User's email address
        phone (StringField): User's phone number
        address (StringField): User's address
        submit (SubmitField): Form submission button

    Validators:
        - Email is required and must be valid
        - Optional fields have length restrictions

    Methods:
        validate_email: Ensures email uniqueness when changed
    """
    first_name = StringField(
        'First Name',
        validators=[Optional(), Length(max=64)]
    )
    last_name = StringField(
        'Last Name',
        validators=[Optional(), Length(max=64)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    phone = StringField(
        'Phone',
        validators=[Optional(), Length(max=20)]
    )
    address = StringField(
        'Address',
        validators=[Optional(), Length(max=256)]
    )
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_email: str, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the form with original email for validation.

        Args:
            original_email (str): The user's current email address
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        logger.debug(f"Initialized UserProfileForm for email: {original_email}")
    
    def validate_email(self, email: StringField) -> None:
        """
        Validate email uniqueness when changed.

        Args:
            email (StringField): The email field to validate

        Raises:
            ValidationError: If new email is already registered
        """
        if email.data != self.original_email:
            logger.debug(f"Validating new email: {email.data}")
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                logger.warning(f"Email already registered: {email.data}")
                raise ValidationError('Please use a different email address.')
            logger.debug(f"Email validation successful: {email.data}")


class ChangePasswordForm(FlaskForm):
    """
    Form for changing password.

    This form allows users to change their password,
    requiring the old password for verification.

    Fields:
        old_password (PasswordField): Current password
        password (PasswordField): New password
        password2 (PasswordField): New password confirmation
        submit (SubmitField): Form submission button

    Validators:
        - All fields are required
        - New password must be at least 6 characters
        - New passwords must match
    """
    old_password = PasswordField(
        'Old Password',
        validators=[DataRequired()]
    )
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=6)
        ]
    )
    password2 = PasswordField(
        'Repeat Password',
        validators=[
            DataRequired(),
            EqualTo('password')
        ]
    )
    submit = SubmitField('Change Password')


class VehicleForm(FlaskForm):
    """
    Form for adding and editing vehicles (admin version).

    This form allows administrators to manage vehicle information,
    including owner assignment and vehicle details.

    Fields:
        owner_id (SelectField): Vehicle owner selection
        make (StringField): Vehicle make
        model (StringField): Vehicle model
        year (IntegerField): Vehicle year
        license_plate (StringField): Vehicle license plate
        vin (StringField): Vehicle identification number
        submit (SubmitField): Form submission button

    Validators:
        - All fields are required
        - Year must be between 1900 and current year + 1
        - VIN must be exactly 17 characters with valid format
        - License plate and VIN must be unique

    Methods:
        validate_vin: Ensures VIN uniqueness
        validate_license_plate: Ensures license plate uniqueness
    """
    owner_id = SelectField(
        'Owner',
        coerce=int,
        validators=[DataRequired()]
    )
    make = StringField(
        'Make',
        validators=[
            DataRequired(),
            Length(
                min=2,
                max=50,
                message='Make must be between 2 and 50 characters.'
            )
        ]
    )
    model = StringField(
        'Model',
        validators=[
            DataRequired(),
            Length(
                min=2,
                max=50,
                message='Model must be between 2 and 50 characters.'
            )
        ]
    )
    year = IntegerField(
        'Year',
        validators=[
            DataRequired(),
            NumberRange(
                min=1900,
                max=datetime.now().year + 1,
                message=f'Year must be between 1900 and {datetime.now().year + 1}.'
            )
        ]
    )
    license_plate = StringField(
        'License Plate',
        validators=[
            DataRequired(),
            Length(
                min=2,
                max=20,
                message='License plate must be between 2 and 20 characters.'
            )
        ]
    )
    vin = StringField(
        'VIN',
        validators=[
            DataRequired(),
            Length(
                min=17,
                max=17,
                message='VIN must be exactly 17 characters.'
            ),
            Regexp(
                r'^[A-HJ-NPR-Z0-9]{17}$',
                message='VIN must contain only valid characters (A-H, J-N, P-Z, 0-9).'
            )
        ]
    )
    submit = SubmitField('Save Vehicle')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the form with vehicle object and owner choices.

        Args:
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments including:
                obj: The vehicle object being edited (optional)
        """
        super(VehicleForm, self).__init__(*args, **kwargs)
        self.vehicle = kwargs.get('obj')
        
        # Get all users for owner selection
        users = User.query.filter_by(role='client').order_by(User.username).all()
        self.owner_id.choices = [
            (user.id, f"{user.username} ({user.first_name} {user.last_name})")
            for user in users
        ]
        logger.debug("Initialized VehicleForm with owner choices")

    def validate_vin(self, vin: StringField) -> None:
        """
        Validate VIN uniqueness.

        Args:
            vin (StringField): The VIN field to validate

        Raises:
            ValidationError: If VIN is already registered
        """
        logger.debug(f"Validating VIN: {vin.data}")
        vehicle = Vehicle.query.filter_by(vin=vin.data).first()
        if vehicle is not None and (self.vehicle is None or vehicle.id != self.vehicle.id):
            logger.warning(f"VIN already registered: {vin.data}")
            raise ValidationError('This VIN is already registered.')
        logger.debug(f"VIN validation successful: {vin.data}")

    def validate_license_plate(self, license_plate: StringField) -> None:
        """
        Validate license plate uniqueness.

        Args:
            license_plate (StringField): The license plate field to validate

        Raises:
            ValidationError: If license plate is already registered
        """
        logger.debug(f"Validating license plate: {license_plate.data}")
        vehicle = Vehicle.query.filter_by(license_plate=license_plate.data).first()
        if vehicle is not None and (self.vehicle is None or vehicle.id != self.vehicle.id):
            logger.warning(f"License plate already registered: {license_plate.data}")
            raise ValidationError('This license plate is already registered.')
        logger.debug(f"License plate validation successful: {license_plate.data}")


class ClientVehicleForm(FlaskForm):
    """Form for adding and editing vehicles (client version)."""
    make = StringField('Make', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Make must be between 2 and 50 characters.')
    ])
    model = StringField('Model', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Model must be between 2 and 50 characters.')
    ])
    year = IntegerField('Year', validators=[
        DataRequired(),
        NumberRange(min=1900, max=datetime.now().year + 1, 
                   message=f'Year must be between 1900 and {datetime.now().year + 1}.')
    ])
    license_plate = StringField('License Plate', validators=[
        DataRequired(),
        Length(min=2, max=20, message='License plate must be between 2 and 20 characters.')
    ])
    vin = StringField('VIN', validators=[
        DataRequired(),
        Length(min=17, max=17, message='VIN must be exactly 17 characters.'),
        Regexp(r'^[A-HJ-NPR-Z0-9]{17}$', 
               message='VIN must contain only valid characters (A-H, J-N, P-Z, 0-9).')
    ])
    submit = SubmitField('Save Vehicle')

    def __init__(self, *args, **kwargs):
        super(ClientVehicleForm, self).__init__(*args, **kwargs)
        self.vehicle = kwargs.get('obj')

    def validate_vin(self, vin):
        """Validate VIN uniqueness."""
        vehicle = Vehicle.query.filter_by(vin=vin.data).first()
        if vehicle is not None and (self.vehicle is None or vehicle.id != self.vehicle.id):
            raise ValidationError('This VIN is already registered.')

    def validate_license_plate(self, license_plate):
        """Validate license plate uniqueness."""
        vehicle = Vehicle.query.filter_by(license_plate=license_plate.data).first()
        if vehicle is not None and (self.vehicle is None or vehicle.id != self.vehicle.id):
            raise ValidationError('This license plate is already registered.')


class UserManagementForm(FlaskForm):
    """Form for managing users."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp('^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers and underscores')
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        Optional(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        Optional(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('client', 'Client'),
        ('employee', 'Employee'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    first_name = StringField('First Name', validators=[Length(max=64)])
    last_name = StringField('Last Name', validators=[Length(max=64)])
    phone = StringField('Phone', validators=[Length(max=20)])
    address = TextAreaField('Address', validators=[Length(max=200)])
    submit = SubmitField('Save')
    
    def __init__(self, original_username=None, original_email=None, is_edit=False, *args, **kwargs):
        super(UserManagementForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        
        # Remove password fields if editing existing user
        if is_edit:
            del self.password
            del self.confirm_password
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')


class AdminPasswordChangeForm(FlaskForm):
    """Form for admin to change user's password."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')


class UserSearchForm(FlaskForm):
    """Form for searching users."""
    search_term = StringField('Search', validators=[Optional()])
    role_filter = SelectField('Role', choices=[('all', 'All'), ('client', 'Client'), ('employee', 'Employee'), ('admin', 'Admin')])
    submit = SubmitField('Search')


class VehicleSearchForm(FlaskForm):
    """Form for searching vehicles."""
    search_term = StringField('Search', validators=[Optional()])
    make_filter = StringField('Make', validators=[Optional()])
    model_filter = StringField('Model', validators=[Optional()])
    year_filter = IntegerField('Year', validators=[Optional()])
    submit = SubmitField('Search')


class ServiceForm(FlaskForm):
    """Form for service management."""
    vehicle_id = SelectField('Vehicle', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    cost = FloatField('Cost', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    scheduled_date = StringField('Scheduled Date', validators=[Optional()])
    submit = SubmitField('Save Service')

    def validate_scheduled_date(self, field):
        """Validate scheduled date format."""
        if field.data:
            try:
                # Try to parse the date in Polish format (DD.MM.YYYY HH:mm)
                datetime.strptime(field.data, '%d.%m.%Y %H:%M')
            except ValueError:
                try:
                    # Try to parse the date in ISO format (YYYY-MM-DD HH:mm)
                    datetime.strptime(field.data, '%Y-%m-%d %H:%M')
                except ValueError:
                    raise ValidationError('Please enter date in format DD.MM.YYYY HH:mm or YYYY-MM-DD HH:mm')


class ServiceRequestForm(FlaskForm):
    """Form for service requests."""
    vehicle_id = SelectField('Vehicle', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, max=1000, message='Description must be between 10 and 1000 characters.')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], validators=[DataRequired()])
    preferred_date = DateTimeField('Preferred Date', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(),
        # Ensure date is not in the past
        lambda form, field: field.data >= datetime.now() if field.data else None
    ])
    additional_notes = TextAreaField('Additional Notes', validators=[
        Optional(),
        Length(max=500, message='Additional notes must be less than 500 characters.')
    ])
    submit = SubmitField('Submit Request')


class ServiceManagementForm(FlaskForm):
    """Form for managing services."""
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    vehicle_id = SelectField('Vehicle', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, max=1000, message='Description must be between 10 and 1000 characters.')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High')
    ], validators=[DataRequired()])
    scheduled_date = StringField('Scheduled Date', validators=[Optional()])
    assigned_employee_id = SelectField('Assign Employee', coerce=int, validators=[Optional()])
    submit = SubmitField('Create Service')

    def __init__(self, *args, **kwargs):
        super(ServiceManagementForm, self).__init__(*args, **kwargs)
        # Populate client choices
        clients = User.query.filter_by(role='client').order_by(User.username).all()
        self.client_id.choices = [(0, '-- Select Client --')] + [(c.id, f"{c.get_full_name()} ({c.email})") for c in clients]
        
        # Initialize vehicle choices with an empty option
        self.vehicle_id.choices = [(0, '-- Select Vehicle --')]
        
        # Populate employee choices with an empty option
        self.assigned_employee_id.choices = [(0, '-- Select Employee (Optional) --')] + [(e.id, e.get_full_name()) for e in User.query.filter_by(role='employee').order_by(User.username).all()]

    def validate_vehicle_id(self, field):
        """Validate that the selected vehicle exists and belongs to the selected client."""
        if not field.data or field.data == 0:
            raise ValidationError('Please select a vehicle.')
        vehicle = Vehicle.query.get(field.data)
        if not vehicle:
            raise ValidationError('Selected vehicle does not exist.')
        if vehicle.owner_id != self.client_id.data:
            raise ValidationError('Selected vehicle does not belong to the selected client.')

    def validate_client_id(self, field):
        """Validate that the selected client exists and is a client."""
        if not field.data or field.data == 0:
            raise ValidationError('Please select a client.')
        client = User.query.get(field.data)
        if not client or client.role != 'client':
            raise ValidationError('Selected user is not a client.')

    def validate_scheduled_date(self, field):
        """Validate scheduled date format."""
        if field.data:
            try:
                # Try to parse the date in Polish format (DD.MM.YYYY HH:mm)
                datetime.strptime(field.data, '%d.%m.%Y %H:%M')
            except ValueError:
                try:
                    # Try to parse the date in ISO format (YYYY-MM-DD HH:mm)
                    datetime.strptime(field.data, '%Y-%m-%d %H:%M')
                except ValueError:
                    raise ValidationError('Please enter date in format DD.MM.YYYY HH:mm or YYYY-MM-DD HH:mm')


class EmployeeVehicleForm(FlaskForm):
    """Form for employee to add/edit vehicles."""
    owner_id = SelectField('Owner', coerce=int, validators=[DataRequired()])
    make = StringField('Make', validators=[DataRequired(), Length(min=1, max=50)])
    model = StringField('Model', validators=[DataRequired(), Length(min=1, max=50)])
    year = IntegerField('Year', validators=[
        DataRequired(),
        NumberRange(min=1900, max=datetime.now().year, message='Year must be between 1900 and current year')
    ])
    license_plate = StringField('License Plate', validators=[DataRequired(), Length(min=1, max=20)])
    vin = StringField('VIN', validators=[DataRequired(), Length(min=17, max=17, message='VIN must be exactly 17 characters')])
    color = StringField('Color', validators=[DataRequired(), Length(min=1, max=30)])
    submit = SubmitField('Save Vehicle')

    def __init__(self, *args, **kwargs):
        super(EmployeeVehicleForm, self).__init__(*args, **kwargs)
        self.vehicle = kwargs.get('obj')
        
        # Get all clients for owner selection
        clients = User.query.filter_by(role='client').order_by(User.username).all()
        self.owner_id.choices = [(client.id, f"{client.username} ({client.first_name} {client.last_name})") for client in clients]

    def validate_license_plate(self, license_plate):
        """Validate that license plate is unique."""
        vehicle = Vehicle.query.filter_by(license_plate=license_plate.data).first()
        if vehicle is not None and (self.vehicle is None or vehicle.id != self.vehicle.id):
            raise ValidationError('This license plate is already registered.')

    def validate_vin(self, vin):
        """Validate that VIN is unique."""
        vehicle = Vehicle.query.filter_by(vin=vin.data).first()
        if vehicle is not None and (self.vehicle is None or vehicle.id != self.vehicle.id):
            raise ValidationError('This VIN is already registered.')


class ServiceEditForm(FlaskForm):
    """
    Form for editing service details.

    This form allows employees to update service information,
    including status, costs, and service details.

    Fields:
        vehicle_id (SelectField): Vehicle selection
        assigned_employee_id (SelectField): Employee assignment
        description (TextAreaField): Service description
        priority (SelectField): Service priority
        status (SelectField): Service status
        scheduled_date (StringField): Scheduled service date
        estimated_cost (FloatField): Estimated service cost
        actual_cost (FloatField): Actual service cost
        diagnosis (TextAreaField): Service diagnosis
        service_plan (TextAreaField): Service plan
        parts_needed (TextAreaField): Required parts
        notes (TextAreaField): Additional notes
        submit (SubmitField): Form submission button

    Validators:
        - Required fields: vehicle_id, description, priority, status
        - Optional fields: scheduled_date, costs, diagnosis, etc.
        - Costs must be non-negative
        - Scheduled date must be in valid format

    Methods:
        validate_scheduled_date: Ensures valid date format
    """
    vehicle_id = SelectField(
        'Vehicle',
        coerce=int,
        validators=[DataRequired()]
    )
    assigned_employee_id = SelectField(
        'Assigned Employee',
        coerce=int,
        validators=[Optional()]
    )
    description = TextAreaField(
        'Description',
        validators=[
            DataRequired(),
            Length(
                min=10,
                max=1000,
                message='Description must be between 10 and 1000 characters long'
            )
        ]
    )
    priority = SelectField(
        'Priority',
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High')
        ],
        validators=[DataRequired()]
    )
    status = SelectField(
        'Status',
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('scheduled', 'Scheduled'),
            ('client_confirmed', 'Client Confirmed'),
            ('waiting_for_vehicle', 'Waiting for Vehicle'),
            ('vehicle_received', 'Vehicle Received'),
            ('diagnosis_pending', 'Diagnosis Pending'),
            ('diagnosis_completed', 'Diagnosis Completed'),
            ('client_consultation', 'Client Consultation'),
            ('client_approved', 'Client Approved'),
            ('waiting_for_parts', 'Waiting for Parts'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('ready_for_payment', 'Ready for Payment'),
            ('payment_received', 'Payment Received'),
            ('ready_for_pickup', 'Ready for Pickup'),
            ('finished', 'Finished'),
            ('cancelled', 'Cancelled')
        ],
        validators=[DataRequired()]
    )
    scheduled_date = StringField(
        'Scheduled Date',
        validators=[Optional()]
    )
    estimated_cost = FloatField(
        'Estimated Cost',
        validators=[Optional(), NumberRange(min=0)]
    )
    actual_cost = FloatField(
        'Actual Cost',
        validators=[Optional(), NumberRange(min=0)]
    )
    diagnosis = TextAreaField(
        'Diagnosis',
        validators=[Optional(), Length(max=1000)]
    )
    service_plan = TextAreaField(
        'Service Plan',
        validators=[Optional(), Length(max=1000)]
    )
    parts_needed = TextAreaField(
        'Parts Needed',
        validators=[Optional(), Length(max=1000)]
    )
    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=1000)]
    )
    submit = SubmitField('Update Service')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the form with vehicle and employee choices.

        Args:
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super(ServiceEditForm, self).__init__(*args, **kwargs)
        # Get all vehicles for the form
        vehicles = Vehicle.query.order_by(Vehicle.make, Vehicle.model).all()
        self.vehicle_id.choices = [
            (v.id, f"{v.make} {v.model} ({v.license_plate})")
            for v in vehicles
        ]
        
        # Get all employees for the form
        employees = User.query.filter_by(role='employee').order_by(User.username).all()
        self.assigned_employee_id.choices = [(0, '-- Select Employee --')] + [
            (e.id, e.get_full_name() or e.username)
            for e in employees
        ]
        logger.debug("Initialized ServiceEditForm with vehicle and employee choices")

    def validate_scheduled_date(self, field: StringField) -> None:
        """
        Validate scheduled date format.

        Args:
            field (StringField): The scheduled date field to validate

        Raises:
            ValidationError: If date format is invalid
        """
        if field.data:
            logger.debug(f"Validating scheduled date: {field.data}")
            try:
                # Try to parse the date in Polish format (DD.MM.YYYY HH:mm)
                datetime.strptime(field.data, '%d.%m.%Y %H:%M')
                logger.debug("Date validated in Polish format")
            except ValueError:
                try:
                    # Try to parse the date in ISO format (YYYY-MM-DD HH:mm)
                    datetime.strptime(field.data, '%Y-%m-%d %H:%M')
                    logger.debug("Date validated in ISO format")
                except ValueError:
                    logger.warning(f"Invalid date format: {field.data}")
                    raise ValidationError(
                        'Please enter date in format DD.MM.YYYY HH:mm or '
                        'YYYY-MM-DD HH:mm'
                    )
