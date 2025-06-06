"""
Admin routes for the CarService application.

This module provides all administrative routes and functionality for the CarService
application. It includes user management, vehicle management, and service management
features accessible only to users with admin privileges.

Routes:
    - Dashboard: Overview of system statistics and recent activities
    - Users: CRUD operations for user management
    - Vehicles: CRUD operations for vehicle management
    - Services: CRUD operations for service management

Dependencies:
    - Flask: Web framework
    - Flask-Login: User session management
    - SQLAlchemy: Database ORM
    - Logging: Application logging
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Vehicle, Service, ServiceHistory
from app.forms import (
    UserManagementForm, AdminPasswordChangeForm, UserSearchForm,
    VehicleForm, VehicleSearchForm, ServiceManagementForm, ServiceEditForm
)
from app.utils import admin_required
from datetime import datetime
import logging

bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Render the admin dashboard with system statistics and recent activities.

    This route displays:
    - Total counts of users, vehicles, and services
    - Recent user registrations
    - Recent service requests
    - Service status statistics
    - User role distribution

    Returns:
        str: Rendered dashboard template with statistics and recent activities

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Admin dashboard accessed by {current_user.username}")
    
    try:
        # Get counts for dashboard
        total_users = User.query.count()
        total_vehicles = Vehicle.query.count()
        total_services = Service.query.count()
        
        # Get recent users and services
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_services = Service.query.order_by(Service.created_at.desc()).limit(5).all()
        
        # Get service statistics
        service_stats = db.session.query(
            Service.status,
            db.func.count(Service.id)
        ).group_by(Service.status).all()
        
        # Get user statistics by role
        user_stats = db.session.query(
            User.role,
            db.func.count(User.id)
        ).group_by(User.role).all()
        
        logger.debug(
            f"Dashboard stats - Users: {total_users}, "
            f"Vehicles: {total_vehicles}, Services: {total_services}"
        )
        
        return render_template(
            'admin/dashboard.html',
            total_users=total_users,
            total_vehicles=total_vehicles,
            total_services=total_services,
            recent_users=recent_users,
            recent_services=recent_services,
            service_stats=service_stats,
            user_stats=user_stats
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('Error loading dashboard statistics', 'error')
        return render_template('admin/dashboard.html')

@bp.route('/users')
@login_required
@admin_required
def users():
    """
    List all users with optional search and filtering capabilities.

    This route provides a paginated list of all users in the system with
    search functionality for username, email, first name, and last name.
    Results can be filtered by user role.

    Query Parameters:
        search_term (str): Optional search term for filtering users
        role_filter (str): Optional role filter ('all', 'admin', 'employee', 'client')

    Returns:
        str: Rendered template with filtered user list

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.debug(f"User list accessed by {current_user.username}")
    
    try:
        # Get search parameters from query string
        search_term = request.args.get('search_term', '')
        role_filter = request.args.get('role_filter', 'all')
        
        # Base query
        query = User.query
        
        # Apply search filters
        if search_term:
            logger.debug(f"Filtering users with search term: {search_term}")
            query = query.filter(
                (User.username.ilike(f'%{search_term}%')) |
                (User.email.ilike(f'%{search_term}%')) |
                (User.first_name.ilike(f'%{search_term}%')) |
                (User.last_name.ilike(f'%{search_term}%'))
            )
        
        if role_filter != 'all':
            logger.debug(f"Filtering users by role: {role_filter}")
            query = query.filter_by(role=role_filter)
        
        # Get users and sort by username
        users = query.order_by(User.username).all()
        logger.debug(f"Found {len(users)} users matching criteria")
        
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logger.error(f"Error retrieving user list: {str(e)}")
        flash('Error retrieving user list', 'error')
        return render_template('admin/users.html', users=[])

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add a new user."""
    logger.debug(f"Add user page accessed by {current_user.username}")
    
    form = UserManagementForm(is_edit=False)
    if form.validate_on_submit():
        logger.info(f"Adding new user by {current_user.username}")
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.address = form.address.data
        
        # Set password if provided, otherwise use default
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.set_password('changeme')
            flash('Default password "changeme" has been set.', 'info')
        
        db.session.add(user)
        db.session.commit()
        flash('User has been added.', 'success')
        logger.info(f"User {user.username} added by {current_user.username}")
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, title='Add User')

@bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit an existing user."""
    logger.debug(f"Edit user page accessed by {current_user.username} for user {id}")
    
    user = User.query.get_or_404(id)
    form = UserManagementForm(original_username=user.username, original_email=user.email, is_edit=True)
    
    if form.validate_on_submit():
        logger.info(f"Updating user {id} by {current_user.username}")
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.address = form.address.data
        
        db.session.commit()
        flash('User has been updated.', 'success')
        logger.info(f"User {user.username} updated by {current_user.username}")
        return redirect(url_for('admin.users'))
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.phone.data = user.phone
        form.address.data = user.address
    
    return render_template('admin/user_form.html', form=form, title='Edit User')

@bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Delete a user."""
    logger.debug(f"Delete user request by {current_user.username} for user {id}")
    
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        logger.warning(f"User {current_user.username} attempted to delete their own account")
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted.', 'success')
    logger.info(f"User {user.username} deleted by {current_user.username}")
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/change-password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_password(id):
    """Change user's password."""
    logger.debug(f"Change password page accessed by {current_user.username} for user {id}")
    
    user = User.query.get_or_404(id)
    form = AdminPasswordChangeForm()
    
    if form.validate_on_submit():
        logger.info(f"Changing password for user {id} by {current_user.username}")
        user.set_password(form.password.data)
        db.session.commit()
        flash('Password has been changed.', 'success')
        logger.info(f"Password changed for user {user.username} by {current_user.username}")
        return redirect(url_for('admin.users'))
    
    return render_template('admin/change_password.html', form=form, user=user)

@bp.route('/vehicles')
@login_required
@admin_required
def vehicles():
    """List all vehicles."""
    logger.debug(f"Vehicle list accessed by {current_user.username}")
    
    # Get search parameters from query string
    search_term = request.args.get('search_term', '')
    make_filter = request.args.get('make_filter', '')
    model_filter = request.args.get('model_filter', '')
    year_filter = request.args.get('year_filter', '')
    
    # Base query
    query = Vehicle.query
    
    # Apply search filters
    if search_term:
        query = query.filter(
            (Vehicle.license_plate.ilike(f'%{search_term}%')) |
            (Vehicle.vin.ilike(f'%{search_term}%'))
        )
    
    if make_filter:
        query = query.filter(Vehicle.make.ilike(f'%{make_filter}%'))
    
    if model_filter:
        query = query.filter(Vehicle.model.ilike(f'%{model_filter}%'))
    
    if year_filter:
        try:
            year = int(year_filter)
            query = query.filter(Vehicle.year == year)
        except ValueError:
            flash('Invalid year format', 'warning')
    
    # Get vehicles and sort by make and model
    vehicles = query.order_by(Vehicle.make, Vehicle.model).all()
    
    return render_template('admin/vehicles.html', vehicles=vehicles)

@bp.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_vehicle():
    """Add a new vehicle."""
    logger.debug(f"Add vehicle page accessed by {current_user.username}")
    
    form = VehicleForm()
    if form.validate_on_submit():
        logger.info(f"Adding new vehicle by {current_user.username}")
        vehicle = Vehicle(
            owner_id=form.owner_id.data,
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            license_plate=form.license_plate.data,
            vin=form.vin.data
        )
        
        db.session.add(vehicle)
        db.session.commit()
        flash('Vehicle has been added.', 'success')
        logger.info(f"Vehicle {vehicle.license_plate} added by {current_user.username}")
        return redirect(url_for('admin.vehicles'))
    
    return render_template('admin/vehicle_form.html', form=form, title='Add Vehicle')

@bp.route('/vehicles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_vehicle(id):
    """Edit an existing vehicle."""
    logger.debug(f"Edit vehicle page accessed by {current_user.username} for vehicle {id}")
    
    vehicle = Vehicle.query.get_or_404(id)
    form = VehicleForm(obj=vehicle)
    
    if form.validate_on_submit():
        logger.info(f"Updating vehicle {id} by {current_user.username}")
        vehicle.owner_id = form.owner_id.data
        vehicle.make = form.make.data
        vehicle.model = form.model.data
        vehicle.year = form.year.data
        vehicle.license_plate = form.license_plate.data
        vehicle.vin = form.vin.data
        
        db.session.commit()
        flash('Vehicle has been updated.', 'success')
        logger.info(f"Vehicle {vehicle.license_plate} updated by {current_user.username}")
        return redirect(url_for('admin.vehicles'))
    
    elif request.method == 'GET':
        form.owner_id.data = vehicle.owner_id
        form.make.data = vehicle.make
        form.model.data = vehicle.model
        form.year.data = vehicle.year
        form.license_plate.data = vehicle.license_plate
        form.vin.data = vehicle.vin
    
    return render_template('admin/vehicle_form.html', form=form, title='Edit Vehicle')

@bp.route('/vehicles/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_vehicle(id):
    """Delete a vehicle."""
    logger.debug(f"Delete vehicle request by {current_user.username} for vehicle {id}")
    
    vehicle = Vehicle.query.get_or_404(id)
    db.session.delete(vehicle)
    db.session.commit()
    flash('Vehicle has been deleted.', 'success')
    logger.info(f"Vehicle {vehicle.license_plate} deleted by {current_user.username}")
    return redirect(url_for('admin.vehicles'))

@bp.route('/services')
@login_required
@admin_required
def services():
    """List all services."""
    logger.debug(f"Service list accessed by {current_user.username}")
    
    # Get filter parameters
    status = request.args.get('status')
    priority = request.args.get('priority')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Service.query.join(Vehicle)
    
    # Filter by status if specified
    if status:
        query = query.filter(Service.status == status)
    
    # Filter by priority if specified
    if priority:
        query = query.filter(Service.priority == priority)
    
    # Filter by date range if specified
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Service.created_at >= start_date)
        except ValueError:
            flash('Invalid start date format', 'warning')
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Service.created_at <= end_date)
        except ValueError:
            flash('Invalid end date format', 'warning')
    
    # Get services and sort by creation date
    services = query.order_by(Service.created_at.desc()).all()
    
    # Sort history entries for each service
    for service in services:
        service.history = sorted(service.history, key=lambda x: x.created_at, reverse=True)
    
    return render_template('admin/services.html', 
                         services=services,
                         statuses=Service.STATUS_TRANSITIONS.keys(),
                         priorities=['low', 'normal', 'high'])

@bp.route('/services/<int:id>')
@login_required
@admin_required
def service_details(id):
    """View service details."""
    service = Service.query.get_or_404(id)
    
    # Get history entries sorted by date
    history_entries = service.history.order_by(ServiceHistory.created_at.desc()).all()
    
    return render_template('admin/service_details.html',
                         service=service,
                         history_entries=history_entries)

@bp.route('/services/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service():
    """Add a new service."""
    logger.debug(f"Add service page accessed by {current_user.username}")
    
    form = ServiceManagementForm()
    
    if request.method == 'POST':
        # Update vehicle choices based on selected client
        client_id = request.form.get('client_id')
        if client_id and client_id != '0':
            vehicles = Vehicle.query.filter_by(owner_id=client_id).order_by(Vehicle.make, Vehicle.model).all()
            form.vehicle_id.choices = [(0, '-- Select Vehicle --')] + [(v.id, f"{v.make} {v.model} ({v.license_plate})") for v in vehicles]
    
    if form.validate_on_submit():
        try:
            # Create service with basic fields
            service = Service(
                client_id=form.client_id.data,
                vehicle_id=form.vehicle_id.data,
                description=form.description.data,
                priority=form.priority.data,
                status='pending'  # Always start with pending status
            )
            
            # Set scheduled date if provided
            if form.scheduled_date.data:
                try:
                    # Try Polish format first
                    scheduled_date = datetime.strptime(form.scheduled_date.data, '%d.%m.%Y %H:%M')
                except ValueError:
                    # Try ISO format
                    scheduled_date = datetime.strptime(form.scheduled_date.data, '%Y-%m-%d %H:%M')
                service.scheduled_date = scheduled_date
            
            # Optionally assign employee if selected (and not the empty option)
            if form.assigned_employee_id.data and form.assigned_employee_id.data != 0:
                service.employee_id = form.assigned_employee_id.data
            
            db.session.add(service)
            db.session.commit()
            
            # Add history entry for service creation
            history = ServiceHistory(
                service_id=service.id,
                user_id=current_user.id,
                description=f"Service created by {current_user.username} with status: {service.status}"
            )
            db.session.add(history)
            db.session.commit()
            
            flash('Service has been added.', 'success')
            return redirect(url_for('admin.services'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the service: {str(e)}', 'error')
            logger.error(f"Error adding service: {str(e)}")
    
    return render_template('admin/service_form.html', form=form, title='Add Service')

@bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(id):
    """
    Edit an existing service request.

    This route allows administrators to modify all aspects of a service request,
    including status, priority, assigned employee, and service details. All changes
    are tracked in the service history.

    Args:
        id (int): The ID of the service to edit

    Returns:
        str: Rendered template for editing the service or redirect to services list

    Raises:
        404: If the service with the given ID is not found
        Exception: Database errors are caught and logged
    """
    logger.debug(f"Edit service page accessed by {current_user.username} for service {id}")
    
    try:
        service = Service.query.get_or_404(id)
        form = ServiceEditForm(obj=service)
        
        if form.validate_on_submit():
            logger.info(f"Updating service {id} by {current_user.username}")
            
            # Track changes for history
            changes = []
            
            # Check if employee has changed
            if service.employee_id != form.assigned_employee_id.data:
                old_employee = User.query.get(service.employee_id) if service.employee_id else None
                new_employee = User.query.get(form.assigned_employee_id.data) if form.assigned_employee_id.data and form.assigned_employee_id.data != 0 else None
                old_name = old_employee.get_full_name() if old_employee else "None"
                new_name = new_employee.get_full_name() if new_employee else "None"
                changes.append(f"Service reassigned from {old_name} to {new_name}")
                service.employee_id = form.assigned_employee_id.data if form.assigned_employee_id.data != 0 else None
            
            # Check if status has changed
            if service.status != form.status.data:
                changes.append(f"Status changed from {service.status} to {form.status.data}")
                service.status = form.status.data
            
            # Check if priority has changed
            if service.priority != form.priority.data:
                changes.append(f"Priority changed from {service.priority} to {form.priority.data}")
                service.priority = form.priority.data
            
            # Check if vehicle has changed
            if service.vehicle_id != form.vehicle_id.data:
                old_vehicle = Vehicle.query.get(service.vehicle_id)
                new_vehicle = Vehicle.query.get(form.vehicle_id.data)
                changes.append(f"Vehicle changed from {old_vehicle.make} {old_vehicle.model} to {new_vehicle.make} {new_vehicle.model}")
                service.vehicle_id = form.vehicle_id.data
            
            # Update other fields
            if service.description != form.description.data:
                changes.append("Description updated")
                service.description = form.description.data
            
            # Handle scheduled date
            if form.scheduled_date.data:
                try:
                    # Try to parse the date in Polish format
                    new_date = datetime.strptime(form.scheduled_date.data, '%d.%m.%Y %H:%M')
                except ValueError:
                    # Try to parse the date in ISO format
                    new_date = datetime.strptime(form.scheduled_date.data, '%Y-%m-%d %H:%M')
                
                if service.scheduled_date != new_date:
                    changes.append("Scheduled date updated")
                    service.scheduled_date = new_date
            elif service.scheduled_date is not None:
                changes.append("Scheduled date removed")
                service.scheduled_date = None
            
            if service.estimated_cost != form.estimated_cost.data:
                changes.append("Estimated cost updated")
                service.estimated_cost = form.estimated_cost.data
            
            if service.actual_cost != form.actual_cost.data:
                changes.append("Actual cost updated")
                service.actual_cost = form.actual_cost.data
            
            if service.diagnosis != form.diagnosis.data:
                changes.append("Diagnosis updated")
                service.diagnosis = form.diagnosis.data
            
            if service.service_plan != form.service_plan.data:
                changes.append("Service plan updated")
                service.service_plan = form.service_plan.data
            
            if service.parts_needed != form.parts_needed.data:
                changes.append("Parts needed updated")
                service.parts_needed = form.parts_needed.data
            
            if service.notes != form.notes.data:
                changes.append("Notes updated")
                service.notes = form.notes.data
            
            # Add history entries for all changes
            if changes:
                history_notes = "Changes made by administrator:\n" + "\n".join(
                    f"- {change}" for change in changes
                )
                history = ServiceHistory(
                    service_id=service.id,
                    user_id=current_user.id,
                    description=history_notes
                )
                db.session.add(history)
                logger.info(f"Added history entry for service {id} with {len(changes)} changes")
            
            try:
                db.session.commit()
                flash('Service has been updated successfully.', 'success')
                logger.info(f"Service {service.id} updated by {current_user.username}")
                return redirect(url_for('admin.services'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error updating service {id}: {str(e)}")
                flash(f'An error occurred while updating the service: {str(e)}', 'error')
        
        elif request.method == 'GET':
            # Pre-fill form with current values
            form.vehicle_id.data = service.vehicle_id
            form.assigned_employee_id.data = service.employee_id or 0
            form.description.data = service.description
            form.priority.data = service.priority
            form.status.data = service.status
            if service.scheduled_date:
                form.scheduled_date.data = service.scheduled_date.strftime('%d.%m.%Y %H:%M')
            form.estimated_cost.data = service.estimated_cost
            form.actual_cost.data = service.actual_cost
            form.diagnosis.data = service.diagnosis
            form.service_plan.data = service.service_plan
            form.parts_needed.data = service.parts_needed
            form.notes.data = service.notes
            logger.debug(f"Pre-filled form for service {id}")
        
        return render_template('admin/service_edit.html', form=form, service=service)
    except Exception as e:
        logger.error(f"Error in edit_service for service {id}: {str(e)}")
        flash('An error occurred while loading the service', 'error')
        return redirect(url_for('admin.services'))

@bp.route('/services/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_service(id):
    """Delete a service."""
    logger.debug(f"Delete service request by {current_user.username} for service {id}")
    
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Service has been deleted.', 'success')
    logger.info(f"Service {service.id} deleted by {current_user.username}")
    return redirect(url_for('admin.services'))

@bp.route('/users/<int:id>/services')
@login_required
@admin_required
def user_services(id):
    """View services for a specific user."""
    user = User.query.get_or_404(id)
    services = Service.query.filter_by(client_id=id).order_by(Service.created_at.desc()).all()
    return render_template('admin/user_services.html', user=user, services=services)

@bp.route('/users/<int:id>/vehicles')
@login_required
@admin_required
def user_vehicles(id):
    """View vehicles for a specific user."""
    user = User.query.get_or_404(id)
    vehicles = Vehicle.query.filter_by(owner_id=id).order_by(Vehicle.created_at.desc()).all()
    return render_template('admin/user_vehicles.html', user=user, vehicles=vehicles)

@bp.route('/users/<int:id>/services/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user_service(id):
    """Add a new service for a specific user."""
    user = User.query.get_or_404(id)
    form = ServiceManagementForm()
    
    # Get user's vehicles for the form
    vehicles = Vehicle.query.filter_by(owner_id=id).all()
    form.vehicle_id.choices = [(v.id, f"{v.make} {v.model} ({v.license_plate})") for v in vehicles]
    
    if form.validate_on_submit():
        try:
            # Create service with basic fields
            service = Service(
                client_id=id,
                vehicle_id=form.vehicle_id.data,
                description=form.description.data,
                priority=form.priority.data,
                status='pending'  # Always start with pending status
            )
            
            # Set scheduled date if provided
            if form.scheduled_date.data:
                try:
                    # Try Polish format first
                    scheduled_date = datetime.strptime(form.scheduled_date.data, '%d.%m.%Y %H:%M')
                except ValueError:
                    # Try ISO format
                    scheduled_date = datetime.strptime(form.scheduled_date.data, '%Y-%m-%d %H:%M')
                service.scheduled_date = scheduled_date
            
            # Optionally assign employee if selected
            if form.assigned_employee_id.data and form.assigned_employee_id.data != 0:
                service.employee_id = form.assigned_employee_id.data
            
            db.session.add(service)
            db.session.commit()
            
            # Add history entry for service creation
            history = ServiceHistory(
                service_id=service.id,
                user_id=current_user.id,
                description=f"Service created by {current_user.username} with status: {service.status}"
            )
            db.session.add(history)
            db.session.commit()
            
            flash('Service has been added.', 'success')
            return redirect(url_for('admin.user_services', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the service: {str(e)}', 'error')
    
    return render_template('admin/service_form.html', form=form, title=f'Add Service for {user.get_full_name() or user.username}')

@bp.route('/users/<int:id>/vehicles/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user_vehicle(id):
    """Add a new vehicle for a specific user."""
    user = User.query.get_or_404(id)
    form = VehicleForm()
    
    if form.validate_on_submit():
        try:
            vehicle = Vehicle(
                owner_id=id,
                make=form.make.data,
                model=form.model.data,
                year=form.year.data,
                license_plate=form.license_plate.data,
                vin=form.vin.data
            )
            db.session.add(vehicle)
            db.session.commit()
            flash('Vehicle has been added.', 'success')
            logger.info(f"Vehicle {vehicle.license_plate} added for user {user.username} by {current_user.username}")
            return redirect(url_for('admin.user_vehicles', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the vehicle: {str(e)}', 'error')
    
    return render_template('admin/vehicle_form.html', form=form, title=f'Add Vehicle for {user.get_full_name() or user.username}')

@bp.route('/api/clients/<int:client_id>/vehicles')
@login_required
@admin_required
def get_client_vehicles(client_id):
    """
    Get vehicles for a specific client via API endpoint.

    This route provides a JSON API endpoint to retrieve all vehicles
    associated with a specific client. The response includes basic
    vehicle information in JSON format.

    Args:
        client_id (int): The ID of the client whose vehicles to retrieve

    Returns:
        JSON: List of vehicles with their details or error message
        Status Code: 200 for success, 404 if client not found, 500 for server errors

    Raises:
        404: If the client with the given ID is not found or is not a client
        Exception: Other errors are caught and logged
    """
    logger.debug(f"API request for client {client_id} vehicles by {current_user.username}")
    
    try:
        # Verify client exists and is a client
        client = User.query.filter_by(id=client_id, role='client').first_or_404()
        
        # Get client's vehicles
        vehicles = Vehicle.query.filter_by(owner_id=client_id).order_by(
            Vehicle.make, Vehicle.model
        ).all()
        
        # Convert to JSON
        vehicles_json = [{
            'id': v.id,
            'make': v.make,
            'model': v.model,
            'license_plate': v.license_plate
        } for v in vehicles]
        
        logger.debug(f"Returning {len(vehicles_json)} vehicles for client {client_id}")
        return jsonify(vehicles_json)
    except Exception as e:
        logger.error(f"Error fetching vehicles for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch vehicles'}), 500
