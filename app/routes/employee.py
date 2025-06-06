"""
Employee routes for the CarService application.

This module handles all employee-specific functionality including:
- Service management (create, update, delete, assign)
- Vehicle management
- User and client management
- Service status tracking and updates
- Service history viewing

Routes:
    - /dashboard: Employee overview
    - /services: Service management
    - /vehicles: Vehicle management
    - /users: User management
    - /services/<id>: Service details and actions

Dependencies:
    - Flask: Web framework and routing
    - Flask-Login: User session management
    - SQLAlchemy: Database operations
    - WTForms: Form handling and validation
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Vehicle, Service, ServiceHistory
from app.forms import (
    ServiceForm, VehicleSearchForm, ServiceManagementForm,
    EmployeeVehicleForm
)
from app.utils import employee_required
from datetime import datetime
from sqlalchemy import or_
import logging

bp = Blueprint('employee', __name__)
logger = logging.getLogger(__name__)

@bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    """
    Render the employee dashboard.

    This route displays the employee's overview page with:
    - Assigned services
    - Service statistics by status
    - Recent activities

    Returns:
        str: Rendered dashboard template with service statistics

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Employee dashboard accessed by {current_user.username} (ID: {current_user.id})")
    logger.debug(f"Dashboard access from IP: {request.remote_addr}")
    
    try:
        # Get assigned services
        assigned_services = Service.query.filter_by(
            employee_id=current_user.id
        ).all()
        
        # Get service statistics
        service_stats = db.session.query(
            Service.status,
            db.func.count(Service.id)
        ).filter_by(employee_id=current_user.id).group_by(
            Service.status
        ).all()
        
        logger.debug(
            f"Dashboard stats - Assigned services: {len(assigned_services)}, "
            f"Status groups: {len(service_stats)}"
        )
        
        return render_template(
            'employee/dashboard.html',
            assigned_services=assigned_services,
            service_stats=service_stats
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('Error loading dashboard statistics', 'error')
        return render_template('employee/dashboard.html')

@bp.route('/services')
@login_required
@employee_required
def services():
    """
    List and filter services.

    This route provides a filtered list of services with options to:
    - Filter by status
    - Filter by priority
    - Filter by date range
    - Sort by creation date

    Query Parameters:
        status (str): Filter by service status
        priority (str): Filter by service priority
        start_date (str): Filter by start date (YYYY-MM-DD)
        end_date (str): Filter by end date (YYYY-MM-DD)

    Returns:
        str: Rendered template with filtered service list

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Service list accessed by {current_user.username}")
    logger.debug(f"Service list access from IP: {request.remote_addr}")
    
    try:
        # Get filter parameters
        status = request.args.get('status')
        priority = request.args.get('priority')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        logger.debug(
            f"Service filters - Status: {status}, Priority: {priority}, "
            f"Start date: {start_date}, End date: {end_date}"
        )
        
        # Base query
        query = Service.query.join(Vehicle)
        
        # Apply filters
        if status:
            query = query.filter(Service.status == status)
        if priority:
            query = query.filter(Service.priority == priority)
        
        # Handle date filters
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Service.created_at >= start_date)
            except ValueError:
                logger.warning(f"Invalid start date format: {start_date}")
                flash('Invalid start date format', 'warning')
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Service.created_at <= end_date)
            except ValueError:
                logger.warning(f"Invalid end date format: {end_date}")
                flash('Invalid end date format', 'warning')
        
        # Get services and sort
        services = query.order_by(Service.created_at.desc()).all()
        
        # Sort history entries
        for service in services:
            service.history = sorted(
                service.history,
                key=lambda x: x.created_at,
                reverse=True
            )
        
        logger.debug(f"Found {len(services)} services matching criteria")
        
        return render_template(
            'employee/services.html',
            services=services,
            statuses=Service.STATUS_TRANSITIONS.keys(),
            priorities=['low', 'normal', 'high']
        )
    except Exception as e:
        logger.error(f"Error retrieving service list: {str(e)}")
        flash('Error retrieving service list', 'error')
        return render_template('employee/services.html', services=[])

@bp.route('/services/add', methods=['GET', 'POST'])
@login_required
@employee_required
def add_service():
    """Add a new service."""
    logger.debug(f"Add service page accessed by {current_user.username}")
    
    form = ServiceForm()
    if form.validate_on_submit():
        logger.info(f"Adding new service by {current_user.username}")
        service = Service(
            vehicle_id=form.vehicle_id.data,
            description=form.description.data,
            cost=form.cost.data,
            status=form.status.data,
            employee_id=current_user.id
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
        
        db.session.add(service)
        db.session.commit()
        flash('Service has been added.', 'success')
        logger.info(f"Service added by {current_user.username}")
        return redirect(url_for('employee.services'))
    
    return render_template('employee/service_form.html', form=form, title='Add Service')

@bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@employee_required
def edit_service(id):
    """Edit an existing service."""
    logger.debug(f"Edit service page accessed by {current_user.username} for service {id}")
    
    service = Service.query.get_or_404(id)
    form = ServiceForm()
    
    if form.validate_on_submit():
        logger.info(f"Updating service {id} by {current_user.username}")
        service.vehicle_id = form.vehicle_id.data
        service.description = form.description.data
        service.cost = form.cost.data
        service.status = form.status.data
        
        db.session.commit()
        flash('Service has been updated.', 'success')
        logger.info(f"Service {id} updated by {current_user.username}")
        return redirect(url_for('employee.services'))
    
    elif request.method == 'GET':
        form.vehicle_id.data = service.vehicle_id
        form.description.data = service.description
        form.cost.data = service.cost
        form.status.data = service.status
    
    return render_template('employee/service_form.html', form=form, title='Edit Service')

@bp.route('/services/<int:id>/delete', methods=['POST'])
@login_required
@employee_required
def delete_service(id):
    """Delete a service."""
    logger.debug(f"Delete service request by {current_user.username} for service {id}")
    
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Service has been deleted.', 'success')
    logger.info(f"Service {id} deleted by {current_user.username}")
    return redirect(url_for('employee.services'))

@bp.route('/users')
@login_required
@employee_required
def users():
    """List all users."""
    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(
            or_(
                User.first_name.ilike(f'%{search_query}%'),
                User.last_name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        users = User.query.all()
    return render_template('employee/users.html', users=users)

@bp.route('/users/<int:id>/services')
@login_required
@employee_required
def user_services(id):
    """View services for a specific user."""
    user = User.query.get_or_404(id)
    services = Service.query.filter_by(client_id=id).order_by(Service.created_at.desc()).all()
    return render_template('employee/user_services.html', user=user, services=services)

@bp.route('/vehicles/<int:id>')
@login_required
@employee_required
def vehicle_details(id):
    """View vehicle details."""
    vehicle = Vehicle.query.get_or_404(id)
    services = Service.query.filter_by(vehicle_id=id).order_by(Service.created_at.desc()).all()
    return render_template('employee/vehicle_details.html', vehicle=vehicle, services=services)

@bp.route('/vehicles')
@login_required
@employee_required
def vehicles():
    """List all vehicles with search functionality."""
    search_query = request.args.get('search', '')
    user_id = request.args.get('user_id')
    
    query = Vehicle.query.join(User, Vehicle.owner_id == User.id)
    if search_query:
        query = query.filter(
            or_(
                Vehicle.license_plate.ilike(f'%{search_query}%'),
                Vehicle.make.ilike(f'%{search_query}%'),
                Vehicle.model.ilike(f'%{search_query}%')
            )
        )
    if user_id:
        try:
            user_id = int(user_id)
            query = query.filter(Vehicle.owner_id == user_id)
        except ValueError:
            flash('Invalid user ID', 'warning')
    
    vehicles = query.all()
    return render_template('employee/vehicles.html', vehicles=vehicles)

@bp.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
@employee_required
def add_vehicle():
    """Add a new vehicle."""
    # Get user_id from query parameters if provided
    user_id = request.args.get('user_id', type=int)
    
    form = EmployeeVehicleForm()
    
    # If user_id is provided in URL, set it as default in the form
    if user_id and request.method == 'GET':
        user = User.query.get(user_id)
        if user and user.role == 'client':
            form.owner_id.data = user_id
    
    if form.validate_on_submit():
        try:
            # Verify that the selected owner is a client
            owner = User.query.get(form.owner_id.data)
            if not owner or owner.role != 'client':
                flash('Invalid owner selected.', 'error')
                return render_template('employee/vehicle_form.html', form=form, title='Add Vehicle')
            
            vehicle = Vehicle(
                owner_id=form.owner_id.data,
                make=form.make.data,
                model=form.model.data,
                year=form.year.data,
                license_plate=form.license_plate.data,
                vin=form.vin.data,
                color=form.color.data
            )
            db.session.add(vehicle)
            db.session.commit()
            logger.info(f'Employee {current_user.username} added new vehicle: {vehicle.license_plate} for owner {owner.username}')
            flash('Vehicle added successfully.', 'success')
            return redirect(url_for('employee.vehicles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error adding vehicle: {str(e)}')
            flash('An error occurred while adding the vehicle. Please try again.', 'error')
    
    return render_template('employee/vehicle_form.html', form=form, title='Add Vehicle')

@bp.route('/vehicles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@employee_required
def edit_vehicle(id):
    """Edit an existing vehicle."""
    vehicle = Vehicle.query.get_or_404(id)
    form = EmployeeVehicleForm(obj=vehicle)
    
    if form.validate_on_submit():
        try:
            # Check if license plate or VIN is being changed and if it's unique
            if form.license_plate.data != vehicle.license_plate:
                existing = Vehicle.query.filter_by(license_plate=form.license_plate.data).first()
                if existing and existing.id != vehicle.id:
                    flash('This license plate is already registered.', 'error')
                    return render_template('employee/vehicle_form.html', form=form, vehicle=vehicle, title='Edit Vehicle')
            
            if form.vin.data != vehicle.vin:
                existing = Vehicle.query.filter_by(vin=form.vin.data).first()
                if existing and existing.id != vehicle.id:
                    flash('This VIN is already registered.', 'error')
                    return render_template('employee/vehicle_form.html', form=form, vehicle=vehicle, title='Edit Vehicle')
            
            vehicle.make = form.make.data
            vehicle.model = form.model.data
            vehicle.year = form.year.data
            vehicle.license_plate = form.license_plate.data
            vehicle.vin = form.vin.data
            vehicle.color = form.color.data
            
            db.session.commit()
            logger.info(f'Employee {current_user.username} edited vehicle: {vehicle.license_plate}')
            flash('Vehicle updated successfully.', 'success')
            return redirect(url_for('employee.vehicles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating vehicle: {str(e)}')
            flash('An error occurred while updating the vehicle. Please try again.', 'error')
    
    return render_template('employee/vehicle_form.html', form=form, vehicle=vehicle, title='Edit Vehicle')

@bp.route('/services/new', methods=['GET', 'POST'])
@login_required
@employee_required
def new_service():
    """Create a new service."""
    user_id = request.args.get('user_id')
    if user_id:
        user = User.query.get_or_404(user_id)
        vehicles = Vehicle.query.filter_by(owner_id=user_id).all()
    else:
        user = None
        vehicles = []

    if request.method == 'POST':
        user_id = request.form['user_id']
        vehicle_id = request.form['vehicle_id']
        description = request.form['description']
        priority = request.form['priority']
        scheduled_date_str = request.form.get('scheduled_date')
        
        try:
            service = Service(
                client_id=user_id,
                vehicle_id=vehicle_id,
                description=description,
                priority=priority,
                status='pending'
            )
            
            # Set scheduled date if provided
            if scheduled_date_str:
                try:
                    # Try Polish format first
                    scheduled_date = datetime.strptime(scheduled_date_str, '%d.%m.%Y %H:%M')
                except ValueError:
                    # Try ISO format
                    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d %H:%M')
                service.scheduled_date = scheduled_date
            
            db.session.add(service)
            db.session.commit()  # First commit to get the service ID
            
            # Add history entry for service creation after service is saved
            history = ServiceHistory(
                service_id=service.id,  # Now service.id is available
                user_id=current_user.id,
                description=f"Service created by {current_user.username}"
            )
            db.session.add(history)
            db.session.commit()
            
            flash('Service created successfully.', 'success')
            return redirect(url_for('employee.services'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating the service: {str(e)}', 'error')
            logger.error(f"Error creating service: {str(e)}")
    
    users = User.query.filter_by(role='client').all()
    return render_template('employee/new_service.html', users=users, selected_user=user, vehicles=vehicles)

@bp.route('/services/<int:id>/manage', methods=['GET', 'POST'])
@login_required
@employee_required
def manage_service(id):
    """
    Manage a service's details and status.

    This route allows employees to:
    - Update service status
    - Modify service details
    - Add diagnosis and service plan
    - Update costs and duration
    - Add notes and parts needed

    Args:
        id (int): The ID of the service to manage

    Returns:
        GET: Rendered service management form
        POST: Redirect to services list on success

    Raises:
        404: If the service is not found
        Exception: If service update fails
    """
    logger.info(f"Service {id} management accessed by {current_user.username}")
    logger.debug(f"Service management access from IP: {request.remote_addr}")
    
    try:
        service = Service.query.get_or_404(id)
        form = ServiceManagementForm(obj=service)
        
        if form.validate_on_submit():
            old_status = service.status
            changes = []
            
            # Track changes for history
            if service.status != form.status.data:
                changes.append(f"Status changed from {old_status} to {form.status.data}")
                service.status = form.status.data
            
            if service.scheduled_date != form.scheduled_date.data:
                changes.append("Scheduled date updated")
                service.scheduled_date = form.scheduled_date.data
            
            if service.diagnosis != form.diagnosis.data:
                changes.append("Diagnosis updated")
                service.diagnosis = form.diagnosis.data
            
            if service.service_plan != form.service_plan.data:
                changes.append("Service plan updated")
                service.service_plan = form.service_plan.data
            
            if service.estimated_cost != form.estimated_cost.data:
                changes.append("Estimated cost updated")
                service.estimated_cost = form.estimated_cost.data
            
            if service.actual_cost != form.actual_cost.data:
                changes.append("Actual cost updated")
                service.actual_cost = form.actual_cost.data
            
            if service.estimated_duration != form.estimated_duration.data:
                changes.append("Estimated duration updated")
                service.estimated_duration = form.estimated_duration.data
            
            if service.parts_needed != form.parts_needed.data:
                changes.append("Parts needed updated")
                service.parts_needed = form.parts_needed.data
            
            if service.notes != form.notes.data:
                changes.append("Notes updated")
                service.notes = form.notes.data
            
            # Handle status change and assignment
            if old_status != service.status:
                service.add_history_entry(
                    f'Status changed from {old_status} to {service.status}',
                    current_user.id
                )
            
            if (old_status == 'pending' and service.status == 'accepted' 
                    and not service.employee_id):
                service.employee_id = current_user.id
                service.add_history_entry(
                    f'Service assigned to {current_user.get_full_name()}',
                    current_user.id
                )
            
            # Add history entry for all changes
            if changes:
                history_notes = "Changes made by employee:\n" + "\n".join(
                    f"- {change}" for change in changes
                )
                service.add_history_entry(history_notes, current_user.id)
            
            try:
                db.session.commit()
                logger.info(
                    f"Service {id} updated by {current_user.username} "
                    f"with {len(changes)} changes"
                )
                flash('Service updated successfully.', 'success')
                return redirect(url_for('employee.services'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error updating service {id}: {str(e)}")
                flash('An error occurred while updating the service.', 'error')
        
        return render_template(
            'employee/manage_service.html',
            service=service,
            form=form
        )
    except Exception as e:
        logger.error(f"Error in manage_service for service {id}: {str(e)}")
        flash('An error occurred while loading the service.', 'error')
        return redirect(url_for('employee.services'))

@bp.route('/services/<int:id>/assign', methods=['POST'])
@login_required
@employee_required
def assign_service(id):
    """Assign or reassign a service to an employee."""
    service = Service.query.get_or_404(id)
    
    # Get employee_id from form
    employee_id = request.form.get('employee_id')
    
    # If no employee_id provided, assign to current user
    if not employee_id:
        employee_id = current_user.id
    
    # If current user is not admin, they can only assign to themselves
    if not current_user.is_admin() and int(employee_id) != current_user.id:
        flash('You can only assign services to yourself.', 'warning')
        return redirect(url_for('employee.services'))
    
    # Get the employee
    employee = User.query.get(employee_id)
    if not employee or not employee.is_employee():
        flash('Invalid employee selected.', 'warning')
        return redirect(url_for('employee.services'))
    
    # Check if service is already assigned to this employee
    if service.employee_id == int(employee_id):
        flash('This service is already assigned to you.', 'info')
        return redirect(url_for('employee.services'))
    
    try:
        service.assign_employee(employee.id, current_user.id)
        flash('Service assigned successfully.', 'success')
    except Exception as e:
        flash(f'Error assigning service: {str(e)}', 'danger')
    
    return redirect(url_for('employee.services'))

@bp.route('/services/<int:id>/accept', methods=['POST'])
@login_required
@employee_required
def accept_service(id):
    """Accept a service request."""
    service = Service.query.get_or_404(id)
    
    if service.status != 'pending':
        flash('This service request cannot be accepted.', 'warning')
        return redirect(url_for('employee.services'))
    
    service.status = 'accepted'
    service.employee_id = current_user.id
    service.add_history_entry(
        f'Service accepted by {current_user.get_full_name()}',
        current_user.id
    )
    
    db.session.commit()
    flash('Service request accepted successfully.', 'success')
    return redirect(url_for('employee.services'))

@bp.route('/services/<int:id>/update', methods=['GET', 'POST'])
@login_required
@employee_required
def update_service(id):
    """Update service details."""
    service = Service.query.get_or_404(id)
    
    # Check if service can be updated
    if not service.can_be_updated():
        flash('This service cannot be updated in its current state.', 'warning')
        return redirect(url_for('employee.services'))
    
    if request.method == 'POST':
        new_status = request.form.get('status')
        
        # Validate status transition
        if not service.can_transition_to(new_status):
            flash('Invalid status transition.', 'danger')
            return redirect(url_for('employee.update_service', id=id))
        
        # Update service details
        try:
            service.validate_costs(
                estimated_cost=request.form.get('estimated_cost'),
                actual_cost=request.form.get('actual_cost')
            )
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('employee.update_service', id=id))
        
        service.diagnosis = request.form.get('diagnosis')
        service.service_plan = request.form.get('service_plan')
        service.parts_needed = request.form.get('parts_needed')
        service.notes = request.form.get('notes')
        
        # Handle status change
        if new_status != service.status:
            service.update_status(new_status, current_user.id)
        
        db.session.commit()
        flash('Service updated successfully.', 'success')
        return redirect(url_for('employee.services'))
    
    # Get available status transitions for the current status
    available_statuses = Service.STATUS_TRANSITIONS.get(service.status, [])
    
    return render_template('employee/update_service.html',
                         service=service,
                         available_statuses=available_statuses)

@bp.route('/services/<int:id>/propose-date', methods=['POST'])
@login_required
@employee_required
def propose_date(id):
    """Propose a new date for a service."""
    service = Service.query.get_or_404(id)
    
    if not service.can_employee_propose_date():
        flash('Cannot propose date in current service state.', 'warning')
        return redirect(url_for('employee.services'))
    
    try:
        scheduled_date = datetime.strptime(request.form['scheduled_date'], '%Y-%m-%dT%H:%M')
        
        service.scheduled_date = scheduled_date
        service.status = Service.STATUS_SCHEDULED
        service.add_history_entry(
            f'Employee proposed new date: {scheduled_date.strftime("%Y-%m-%d %H:%M")}',
            current_user.id
        )
        db.session.commit()
        
        flash('Date proposal has been submitted.', 'success')
    except ValueError:
        flash('Invalid date format. Please use the date picker.', 'danger')
    except Exception as e:
        flash('An error occurred while processing your request.', 'danger')
        logger.error(f"Error in propose_date: {str(e)}")
    
    return redirect(url_for('employee.services'))

@bp.route('/services/<int:id>/reject', methods=['POST'])
@login_required
@employee_required
def reject_service(id):
    """Reject a service request."""
    service = Service.query.get_or_404(id)
    
    if service.status != 'pending':
        flash('Can only reject pending services.', 'warning')
        return redirect(url_for('employee.services'))
    
    rejection_reason = request.form.get('rejection_reason', '')
    if not rejection_reason:
        flash('Please provide a reason for rejection.', 'warning')
        return redirect(url_for('employee.services'))
    
    service.status = 'cancelled'
    service.add_history_entry(
        f'Service rejected by employee. Reason: {rejection_reason}',
        current_user.id
    )
    db.session.commit()
    
    flash('Service has been rejected.', 'success')
    return redirect(url_for('employee.services'))

@bp.route('/services/<int:id>/history')
@login_required
@employee_required
def service_history(id):
    """View service history."""
    service = Service.query.get_or_404(id)
    
    # Get history entries sorted by date
    history_entries = service.history.order_by(ServiceHistory.created_at.desc()).all()
    
    return render_template('employee/service_history.html',
                         service=service,
                         history_entries=history_entries)

@bp.route('/services/<int:id>/update-status', methods=['POST'])
@login_required
@employee_required
def update_service_status(id):
    """Update service status."""
    service = Service.query.get_or_404(id)
    
    new_status = request.form.get('new_status')
    status_note = request.form.get('status_note')
    
    if not new_status or not status_note:
        flash('Please provide both new status and status note.', 'warning')
        return redirect(url_for('employee.service_details', id=id))
    
    old_status = service.status
    service.status = new_status
    service.add_history_entry(
        f'Status changed from {old_status} to {new_status}. Note: {status_note}',
        current_user.id
    )
    
    db.session.commit()
    flash('Service status has been updated.', 'success')
    return redirect(url_for('employee.service_details', id=id))

@bp.route('/services/<int:id>')
@login_required
@employee_required
def service_details(id):
    """View service details."""
    service = Service.query.get_or_404(id)
    
    # Get history entries sorted by date
    history_entries = service.history.order_by(ServiceHistory.created_at.desc()).all()
    
    return render_template('employee/service_details.html',
                         service=service,
                         history_entries=history_entries)

@bp.route('/api/users/<int:user_id>/vehicles')
@login_required
@employee_required
def get_user_vehicles(user_id):
    """Get vehicles for a specific user."""
    try:
        user = User.query.get_or_404(user_id)
        vehicles = Vehicle.query.filter_by(owner_id=user_id).all()
        
        return jsonify([{
            'id': vehicle.id,
            'make': vehicle.make,
            'model': vehicle.model,
            'license_plate': vehicle.license_plate
        } for vehicle in vehicles])
    except Exception as e:
        logger.error(f"Error fetching vehicles for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch vehicles'}), 500
