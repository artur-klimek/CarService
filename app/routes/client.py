"""
Client routes for the CarService application.

This module handles all client-specific functionality including:
- Vehicle management (add, edit, delete, list)
- Service request management
- Service status tracking and updates
- Payment processing
- Service history viewing

Routes:
    - /dashboard: Client overview
    - /vehicles: Vehicle management
    - /services: Service management
    - /service-request: New service requests
    - /services/<id>: Service details and actions

Dependencies:
    - Flask: Web framework and routing
    - Flask-Login: User session management
    - SQLAlchemy: Database operations
    - WTForms: Form handling and validation
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Vehicle, Service, ServiceHistory
from app.forms import ClientVehicleForm, ServiceRequestForm
from app.utils import client_required
from datetime import datetime
import logging

client_bp = Blueprint('client', __name__)
logger = logging.getLogger(__name__)

@client_bp.route('/dashboard')
@login_required
@client_required
def dashboard():
    """
    Render the client dashboard.

    This route displays the client's overview page with summary
    information about their vehicles and services.

    Returns:
        str: Rendered dashboard template

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Client dashboard accessed by {current_user.username} (ID: {current_user.id})")
    logger.debug(f"Dashboard access from IP: {request.remote_addr}")
    return render_template('client/dashboard.html')

@client_bp.route('/vehicles')
@login_required
@client_required
def vehicles():
    """
    List all vehicles owned by the current client.

    This route displays a list of all vehicles registered to the
    currently logged-in client.

    Returns:
        str: Rendered template with list of vehicles

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Vehicle list accessed by {current_user.username} (ID: {current_user.id})")
    logger.debug(f"Vehicle list access from IP: {request.remote_addr}")
    
    try:
        vehicles = Vehicle.query.filter_by(owner_id=current_user.id).all()
        logger.debug(f"Found {len(vehicles)} vehicles for client {current_user.username}")
        return render_template('client/vehicles.html', vehicles=vehicles)
    except Exception as e:
        logger.error(f"Error retrieving vehicle list: {str(e)}")
        flash('Error retrieving vehicle list', 'error')
        return render_template('client/vehicles.html', vehicles=[])

@client_bp.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
@client_required
def add_vehicle():
    """
    Add a new vehicle to the client's account.

    This route handles the creation of new vehicle records for the
    currently logged-in client.

    Methods:
        GET: Display vehicle addition form
        POST: Process vehicle addition form

    Returns:
        GET: Rendered vehicle form template
        POST: Redirect to vehicle list on success

    Raises:
        None: All errors are handled internally with appropriate logging
    """
    logger.info(f"Add vehicle page accessed by {current_user.username}")
    logger.debug(f"Add vehicle access from IP: {request.remote_addr}")
    
    form = ClientVehicleForm()
    if form.validate_on_submit():
        try:
            vehicle = Vehicle(
                owner_id=current_user.id,
                make=form.make.data,
                model=form.model.data,
                year=form.year.data,
                license_plate=form.license_plate.data,
                vin=form.vin.data
            )
            db.session.add(vehicle)
            db.session.commit()
            
            logger.info(
                f"Vehicle added: {vehicle.make} {vehicle.model} "
                f"({vehicle.license_plate}) by user {current_user.username}"
            )
            logger.debug(f"New vehicle ID: {vehicle.id}")
            
            flash('Vehicle has been added successfully.', 'success')
            return redirect(url_for('client.vehicles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding vehicle: {str(e)}")
            flash('An error occurred while adding the vehicle. Please try again.', 'error')
    
    return render_template('client/vehicle_form.html', title='Add Vehicle', form=form)

@client_bp.route('/vehicles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@client_required
def edit_vehicle(id):
    """
    Edit an existing vehicle.

    This route allows clients to modify their vehicle information.
    Only vehicles owned by the current client can be edited.

    Args:
        id (int): The ID of the vehicle to edit

    Returns:
        GET: Rendered vehicle edit form
        POST: Redirect to vehicle list on success

    Raises:
        403: If the vehicle does not belong to the current client
        404: If the vehicle is not found
    """
    logger.info(f"Edit vehicle page accessed by {current_user.username} for vehicle {id}")
    logger.debug(f"Edit vehicle access from IP: {request.remote_addr}")
    
    try:
        vehicle = Vehicle.query.get_or_404(id)
        
        # Ensure the vehicle belongs to the current user
        if vehicle.owner_id != current_user.id:
            logger.warning(
                f"Unauthorized edit attempt for vehicle {id} "
                f"by user {current_user.username}"
            )
            abort(403)
        
        form = ClientVehicleForm(obj=vehicle)
        if form.validate_on_submit():
            try:
                vehicle.make = form.make.data
                vehicle.model = form.model.data
                vehicle.year = form.year.data
                vehicle.license_plate = form.license_plate.data
                vehicle.vin = form.vin.data
                
                db.session.commit()
                
                logger.info(
                    f"Vehicle updated: {vehicle.make} {vehicle.model} "
                    f"({vehicle.license_plate}) by user {current_user.username}"
                )
                logger.debug(f"Updated vehicle ID: {vehicle.id}")
                
                flash('Vehicle has been updated successfully.', 'success')
                return redirect(url_for('client.vehicles'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating vehicle: {str(e)}")
                flash('An error occurred while updating the vehicle. Please try again.', 'error')
        
        return render_template(
            'client/vehicle_form.html',
            title='Edit Vehicle',
            form=form,
            vehicle=vehicle
        )
    except Exception as e:
        logger.error(f"Error in edit_vehicle for vehicle {id}: {str(e)}")
        flash('An error occurred while loading the vehicle.', 'error')
        return redirect(url_for('client.vehicles'))

@client_bp.route('/vehicles/<int:id>/delete', methods=['POST'])
@login_required
@client_required
def delete_vehicle(id):
    """Delete a vehicle."""
    logger.info(f"Delete vehicle request by {current_user.username} for vehicle {id}")
    vehicle = Vehicle.query.get_or_404(id)
    if vehicle.owner_id != current_user.id:
        flash('You do not have permission to delete this vehicle.', 'danger')
        return redirect(url_for('client.vehicles'))
    
    db.session.delete(vehicle)
    db.session.commit()
    flash('Vehicle has been deleted.', 'success')
    return redirect(url_for('client.vehicles'))

@client_bp.route('/services')
@login_required
@client_required
def services():
    """List client's services."""
    logger.info(f"Service list accessed by {current_user.username}")
    
    # Get status filter from query parameters
    status = request.args.get('status')
    
    # Base query
    query = Service.query.join(Vehicle).filter(Vehicle.owner_id == current_user.id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Service.status == status)
    
    # Get services and sort by creation date
    services = query.order_by(Service.created_at.desc()).all()
    
    # Sort history entries for each service
    for service in services:
        service.history = sorted(service.history, key=lambda x: x.created_at, reverse=True)
    
    return render_template('client/services.html', services=services)

@client_bp.route('/service-request', methods=['GET', 'POST'])
@login_required
@client_required
def service_request():
    """Create a new service request."""
    vehicle_id = request.args.get('vehicle_id')
    if not vehicle_id:
        flash('Please select a vehicle first.', 'warning')
        return redirect(url_for('client.vehicles'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.owner_id != current_user.id:
        flash('You do not have permission to create a service for this vehicle.', 'danger')
        return redirect(url_for('client.vehicles'))
    
    if request.method == 'POST':
        description = request.form.get('description')
        preferred_date = request.form.get('preferred_date')
        priority = request.form.get('priority', 'normal')
        
        if not description:
            flash('Please provide a description of the service needed.', 'warning')
            return redirect(url_for('client.service_request', vehicle_id=vehicle_id))
        
        try:
            preferred_date = datetime.strptime(preferred_date, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            flash('Invalid date format.', 'warning')
            return redirect(url_for('client.service_request', vehicle_id=vehicle_id))
        
        service = Service(
            client_id=current_user.id,
            vehicle_id=vehicle_id,
            description=description,
            preferred_date=preferred_date,
            priority=priority,
            status='pending'
        )
        
        db.session.add(service)
        db.session.commit()
        
        # Add initial history entry
        service.add_history_entry('Service request created', current_user.id)
        db.session.commit()
        
        flash('Service request has been submitted successfully.', 'success')
        return redirect(url_for('client.services'))
    
    return render_template('client/service_request.html', vehicle=vehicle)

@client_bp.route('/services/<int:id>/confirm', methods=['POST'])
@login_required
@client_required
def confirm_service(id):
    """Confirm a scheduled service."""
    service = Service.query.get_or_404(id)
    if service.client_id != current_user.id:
        flash('You do not have permission to confirm this service.', 'danger')
        return redirect(url_for('client.services'))
    
    if service.status != 'scheduled':
        flash('This service cannot be confirmed in its current state.', 'warning')
        return redirect(url_for('client.service_details', id=id))
    
    service.status = 'client_confirmed'
    service.add_history_entry('Client confirmed the service', current_user.id)
    db.session.commit()
    
    flash('Service has been confirmed.', 'success')
    return redirect(url_for('client.service_details', id=id))

@client_bp.route('/services/<int:id>/request-date-change', methods=['POST'])
@login_required
@client_required
def request_date_change(id):
    """Request a date change for a service."""
    service = Service.query.get_or_404(id)
    if service.client_id != current_user.id:
        flash('You do not have permission to modify this service.', 'danger')
        return redirect(url_for('client.services'))
    
    if service.status != 'scheduled':
        flash('Date changes can only be requested for scheduled services.', 'warning')
        return redirect(url_for('client.service_details', id=id))
    
    try:
        new_date = datetime.strptime(request.form['new_date'], '%Y-%m-%dT%H:%M')
        change_reason = request.form.get('change_reason', '')
        
        if not change_reason:
            flash('Please provide a reason for the date change.', 'warning')
            return redirect(url_for('client.service_details', id=id))
        
        service.preferred_date = new_date
        service.status = 'pending'
        service.add_history_entry(
            f'Client requested date change to {new_date.strftime("%Y-%m-%d %H:%M")}. Reason: {change_reason}',
            current_user.id
        )
        db.session.commit()
        
        flash('Date change request has been submitted.', 'success')
    except ValueError:
        flash('Invalid date format. Please use the date picker.', 'danger')
    except Exception as e:
        flash('An error occurred while processing your request.', 'danger')
        logger.error(f"Error in request_date_change: {str(e)}")
    
    return redirect(url_for('client.service_details', id=id))

@client_bp.route('/services/<int:id>/cancel', methods=['POST'])
@login_required
@client_required
def cancel_service(id):
    """Cancel a service."""
    service = Service.query.get_or_404(id)
    if service.client_id != current_user.id:
        abort(403)
    
    cancellation_reason = request.form.get('cancellation_reason')
    if not cancellation_reason:
        flash('Please provide a reason for cancellation.', 'danger')
        return redirect(url_for('client.service_details', id=id))
    
    service.status = 'cancelled'
    service.add_history_entry(f'Service cancelled by client. Reason: {cancellation_reason}', current_user.id)
    db.session.commit()
    
    flash('Service has been cancelled.', 'success')
    return redirect(url_for('client.services'))

@client_bp.route('/services/<int:id>/approve', methods=['POST'])
@login_required
@client_required
def approve_service(id):
    """Approve a service plan."""
    service = Service.query.get_or_404(id)
    if service.client_id != current_user.id:
        flash('You do not have permission to approve this service.', 'danger')
        return redirect(url_for('client.services'))
    
    if service.status != 'diagnosis_completed':
        flash('Service plan can only be approved after diagnosis is completed.', 'warning')
        return redirect(url_for('client.service_details', id=id))
    
    service.status = 'client_approved'
    service.add_history_entry('Client approved the service plan', current_user.id)
    db.session.commit()
    
    flash('Service plan has been approved.', 'success')
    return redirect(url_for('client.service_details', id=id))

@client_bp.route('/services/<int:id>/request-changes', methods=['POST'])
@login_required
@client_required
def request_changes(id):
    """Request changes to a service plan."""
    service = Service.query.get_or_404(id)
    if service.client_id != current_user.id:
        flash('You do not have permission to modify this service.', 'danger')
        return redirect(url_for('client.services'))
    
    if service.status != 'diagnosis_completed':
        flash('Changes can only be requested after diagnosis is completed.', 'warning')
        return redirect(url_for('client.service_details', id=id))
    
    change_request = request.form['change_request']
    service.status = 'client_consultation'
    service.add_history_entry(f'Client requested changes: {change_request}', current_user.id)
    db.session.commit()
    
    flash('Change request has been submitted.', 'success')
    return redirect(url_for('client.service_details', id=id))

@client_bp.route('/services/<int:id>/make-payment', methods=['POST'])
@login_required
@client_required
def make_payment(id):
    """
    Process payment for a completed service.

    This route handles the payment confirmation for a service that
    is ready for payment. It updates the service status and records
    the payment method.

    Args:
        id (int): The ID of the service to pay for

    Returns:
        Redirect to service details page

    Raises:
        404: If the service is not found
        Exception: If payment processing fails
    """
    logger.info(f"Payment attempt for service {id} by {current_user.username}")
    logger.debug(f"Payment attempt from IP: {request.remote_addr}")
    
    try:
        service = Service.query.get_or_404(id)
        
        # Verify ownership and status
        if service.client_id != current_user.id:
            logger.warning(
                f"Unauthorized payment attempt for service {id} "
                f"by user {current_user.username}"
            )
            flash('You do not have permission to make payment for this service.', 'danger')
            return redirect(url_for('client.services'))
        
        if service.status != 'ready_for_payment':
            logger.warning(
                f"Invalid payment attempt for service {id} "
                f"in status {service.status}"
            )
            flash('Payment can only be made when service is ready for payment.', 'warning')
            return redirect(url_for('client.service_details', id=id))
        
        payment_method = request.form['payment_method']
        service.status = 'payment_received'
        service.add_history_entry(
            f'Payment received via {payment_method}',
            current_user.id
        )
        db.session.commit()
        
        logger.info(
            f"Payment received for service {id} via {payment_method} "
            f"by user {current_user.username}"
        )
        logger.debug(f"Payment processed for service {id}")
        
        flash('Payment has been received.', 'success')
        return redirect(url_for('client.service_details', id=id))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing payment for service {id}: {str(e)}")
        flash('An error occurred while processing your payment.', 'error')
        return redirect(url_for('client.service_details', id=id))

@client_bp.route('/services/<int:id>/confirm-pickup', methods=['POST'])
@login_required
@client_required
def confirm_pickup(id):
    """Confirm vehicle pickup."""
    service = Service.query.get_or_404(id)
    if service.client_id != current_user.id:
        flash('You do not have permission to confirm pickup for this service.', 'danger')
        return redirect(url_for('client.services'))
    
    if service.status != 'ready_for_pickup':
        flash('Pickup can only be confirmed when service is ready for pickup.', 'warning')
        return redirect(url_for('client.service_details', id=id))
    
    service.status = 'finished'
    service.add_history_entry('Client confirmed vehicle pickup', current_user.id)
    db.session.commit()
    
    flash('Vehicle pickup has been confirmed.', 'success')
    return redirect(url_for('client.services'))

@client_bp.route('/services/<int:id>')
@login_required
@client_required
def service_details(id):
    """View service details."""
    service = Service.query.get_or_404(id)
    if service.client_id != current_user.id:
        flash('You do not have permission to view this service.', 'danger')
        return redirect(url_for('client.services'))
    
    # Sort history entries by date
    service.history = sorted(service.history, key=lambda x: x.created_at, reverse=True)
    
    return render_template('client/service_details.html', service=service)

@client_bp.route('/services/<int:id>/history')
@login_required
@client_required
def service_history(id):
    """View service history."""
    service = Service.query.get_or_404(id)
    
    # Ensure the service belongs to the current user
    if service.client_id != current_user.id:
        flash('You do not have permission to view this service.', 'danger')
        return redirect(url_for('client.services'))
    
    # Get history entries sorted by date
    history_entries = service.history.order_by(ServiceHistory.created_at.desc()).all()
    
    return render_template('client/service_history.html',
                         service=service,
                         history_entries=history_entries)
