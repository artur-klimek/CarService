"""
User management routes for the CarService application.

This module handles user-specific functionality including:
- Profile management (view, update)
- Password changes
- Vehicle management (add, edit, delete, list)
- User preferences and settings

Routes:
    - /profile: User profile management
    - /vehicles: Vehicle listing and management
    - /vehicles/add: Add new vehicle
    - /vehicles/<id>/edit: Edit existing vehicle
    - /vehicles/<id>/delete: Delete vehicle

Dependencies:
    - Flask: Web framework and routing
    - Flask-Login: User session management
    - SQLAlchemy: Database operations
    - WTForms: Form handling and validation
    - Custom Logger: Application logging utility
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Vehicle
from app.forms import (
    UserProfileForm, ChangePasswordForm, VehicleForm
)
from app.utils.logger import Logger
import logging

# Initialize blueprint and logger
bp = Blueprint('user', __name__)
logger = Logger().get_logger()

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Manage user profile information and password changes.

    This route handles both profile updates and password changes through
    separate forms. It ensures data validation and proper error handling.

    Methods:
        GET: Display profile and password change forms
        POST: Process form submissions

    Returns:
        GET: Rendered profile template with forms
        POST: Redirect to profile page on success

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Profile page accessed by {current_user.username} (ID: {current_user.id})")
    logger.debug(f"Profile access from IP: {request.remote_addr}")
    
    try:
        profile_form = UserProfileForm(original_email=current_user.email)
        password_form = ChangePasswordForm()
        
        # Handle profile form submission
        if profile_form.validate_on_submit():
            logger.info(f"Profile update requested by {current_user.username}")
            
            try:
                current_user.first_name = profile_form.first_name.data
                current_user.last_name = profile_form.last_name.data
                current_user.email = profile_form.email.data
                current_user.phone = profile_form.phone.data
                current_user.address = profile_form.address.data
                
                db.session.commit()
                flash('Your profile has been updated.', 'success')
                logger.info(
                    f"Profile updated for user {current_user.username} - "
                    f"Name: {current_user.get_full_name()}, "
                    f"Email: {current_user.email}"
                )
                return redirect(url_for('user.profile'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating profile: {str(e)}")
                flash('An error occurred while updating your profile.', 'error')
        
        # Handle password form submission
        if password_form.validate_on_submit():
            logger.info(f"Password change requested by {current_user.username}")
            
            try:
                if current_user.check_password(password_form.current_password.data):
                    current_user.set_password(password_form.new_password.data)
                    db.session.commit()
                    flash('Your password has been updated.', 'success')
                    logger.info(f"Password updated for user {current_user.username}")
                else:
                    flash('Current password is incorrect.', 'danger')
                    logger.warning(
                        f"Failed password change attempt for user "
                        f"{current_user.username} from IP: {request.remote_addr}"
                    )
                return redirect(url_for('user.profile'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error changing password: {str(e)}")
                flash('An error occurred while changing your password.', 'error')
        
        # Populate form fields on GET request
        elif request.method == 'GET':
            profile_form.first_name.data = current_user.first_name
            profile_form.last_name.data = current_user.last_name
            profile_form.email.data = current_user.email
            profile_form.phone.data = current_user.phone
            profile_form.address.data = current_user.address
        
        return render_template(
            'user/profile.html',
            profile_form=profile_form,
            password_form=password_form
        )
    except Exception as e:
        logger.error(f"Error in profile route: {str(e)}")
        flash('An error occurred while loading your profile.', 'error')
        return redirect(url_for('main.index'))

@bp.route('/vehicles')
@login_required
def vehicles():
    """
    Display the user's registered vehicles.

    This route lists all vehicles owned by the current user,
    with appropriate access control checks.

    Returns:
        str: Rendered template with vehicle list

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Vehicles list accessed by {current_user.username}")
    logger.debug(f"Vehicles list access from IP: {request.remote_addr}")
    
    try:
        vehicles = current_user.get_vehicles()
        logger.debug(f"Found {len(vehicles)} vehicles for user {current_user.username}")
        return render_template('user/vehicles.html', vehicles=vehicles)
    except Exception as e:
        logger.error(f"Error retrieving vehicles: {str(e)}")
        flash('Error loading vehicles list', 'error')
        return render_template('user/vehicles.html', vehicles=[])

@bp.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    """
    Add a new vehicle to the user's account.

    This route handles the vehicle registration process, including:
    - Vehicle limit validation
    - Form validation
    - Database operations

    Returns:
        GET: Rendered vehicle form template
        POST: Redirect to vehicles list on success

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Add vehicle page accessed by {current_user.username}")
    logger.debug(f"Add vehicle access from IP: {request.remote_addr}")
    
    try:
        if not current_user.can_add_vehicle():
            logger.warning(
                f"Vehicle limit exceeded for user {current_user.username} "
                f"(ID: {current_user.id})"
            )
            flash('You have reached the maximum number of vehicles allowed.', 'danger')
            return redirect(url_for('user.vehicles'))
        
        form = VehicleForm()
        
        if form.validate_on_submit():
            logger.info(f"New vehicle submission by {current_user.username}")
            
            try:
                vehicle = Vehicle(
                    owner_id=current_user.id,
                    make=form.make.data,
                    model=form.model.data,
                    year=form.year.data,
                    vin=form.vin.data,
                    license_plate=form.license_plate.data,
                    color=form.color.data,
                    mileage=form.mileage.data
                )
                
                db.session.add(vehicle)
                db.session.commit()
                
                logger.info(
                    f"Vehicle added for user {current_user.username} - "
                    f"Make: {vehicle.make}, Model: {vehicle.model}, "
                    f"License: {vehicle.license_plate}"
                )
                flash('Vehicle has been added.', 'success')
                return redirect(url_for('user.vehicles'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error adding vehicle: {str(e)}")
                flash('An error occurred while adding the vehicle.', 'error')
        
        return render_template('user/vehicle_form.html', form=form, title='Add Vehicle')
    except Exception as e:
        logger.error(f"Error in add_vehicle route: {str(e)}")
        flash('An error occurred while loading the form.', 'error')
        return redirect(url_for('user.vehicles'))

@bp.route('/vehicles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vehicle(id):
    """
    Edit an existing vehicle's details.

    This route handles vehicle updates with proper access control
    and validation checks.

    Args:
        id (int): The ID of the vehicle to edit

    Returns:
        GET: Rendered vehicle edit form
        POST: Redirect to vehicles list on success

    Raises:
        404: If the vehicle is not found
        None: Other errors are handled internally with appropriate logging
    """
    logger.info(f"Edit vehicle page accessed by {current_user.username} for vehicle {id}")
    logger.debug(f"Edit vehicle access from IP: {request.remote_addr}")
    
    try:
        vehicle = Vehicle.query.get_or_404(id)
        
        # Check permissions
        if vehicle.owner_id != current_user.id and not current_user.can_manage_vehicles():
            logger.warning(
                f"Unauthorized vehicle edit attempt by {current_user.username} "
                f"for vehicle {id}"
            )
            flash('You do not have permission to edit this vehicle.', 'danger')
            return redirect(url_for('user.vehicles'))
        
        form = VehicleForm(
            original_vin=vehicle.vin,
            original_license_plate=vehicle.license_plate
        )
        
        if form.validate_on_submit():
            logger.info(f"Vehicle update submitted by {current_user.username}")
            
            try:
                vehicle.make = form.make.data
                vehicle.model = form.model.data
                vehicle.year = form.year.data
                vehicle.vin = form.vin.data
                vehicle.license_plate = form.license_plate.data
                vehicle.color = form.color.data
                vehicle.mileage = form.mileage.data
                
                db.session.commit()
                
                logger.info(
                    f"Vehicle {id} updated by {current_user.username} - "
                    f"Make: {vehicle.make}, Model: {vehicle.model}, "
                    f"License: {vehicle.license_plate}"
                )
                flash('Vehicle has been updated.', 'success')
                return redirect(url_for('user.vehicles'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating vehicle: {str(e)}")
                flash('An error occurred while updating the vehicle.', 'error')
        
        elif request.method == 'GET':
            form.make.data = vehicle.make
            form.model.data = vehicle.model
            form.year.data = vehicle.year
            form.vin.data = vehicle.vin
            form.license_plate.data = vehicle.license_plate
            form.color.data = vehicle.color
            form.mileage.data = vehicle.mileage
        
        return render_template(
            'user/vehicle_form.html',
            form=form,
            title='Edit Vehicle'
        )
    except Exception as e:
        logger.error(f"Error in edit_vehicle route: {str(e)}")
        flash('An error occurred while loading the form.', 'error')
        return redirect(url_for('user.vehicles'))

@bp.route('/vehicles/<int:id>/delete', methods=['POST'])
@login_required
def delete_vehicle(id):
    """
    Delete a vehicle from the user's account.

    This route handles vehicle deletion with proper access control
    and validation checks.

    Args:
        id (int): The ID of the vehicle to delete

    Returns:
        redirect: Redirect to vehicles list

    Raises:
        404: If the vehicle is not found
        None: Other errors are handled internally with appropriate logging
    """
    logger.info(f"Delete vehicle request by {current_user.username} for vehicle {id}")
    logger.debug(f"Delete vehicle request from IP: {request.remote_addr}")
    
    try:
        vehicle = Vehicle.query.get_or_404(id)
        
        # Check permissions
        if vehicle.owner_id != current_user.id and not current_user.can_manage_vehicles():
            logger.warning(
                f"Unauthorized vehicle deletion attempt by {current_user.username} "
                f"for vehicle {id}"
            )
            flash('You do not have permission to delete this vehicle.', 'danger')
            return redirect(url_for('user.vehicles'))
        
        try:
            vehicle_details = (
                f"Make: {vehicle.make}, Model: {vehicle.model}, "
                f"License: {vehicle.license_plate}"
            )
            db.session.delete(vehicle)
            db.session.commit()
            
            logger.info(
                f"Vehicle {id} deleted by {current_user.username} - {vehicle_details}"
            )
            flash('Vehicle has been deleted.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting vehicle: {str(e)}")
            flash('An error occurred while deleting the vehicle.', 'error')
        
        return redirect(url_for('user.vehicles'))
    except Exception as e:
        logger.error(f"Error in delete_vehicle route: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
        return redirect(url_for('user.vehicles'))
