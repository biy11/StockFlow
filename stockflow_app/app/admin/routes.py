# app/admin/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, Order, DailyOrder, DailyOrderUpdate
from app import db, socketio
from datetime import datetime
import pandas as pd

# Define the Blueprint here
admin = Blueprint('admin', __name__, template_folder='templates')

# Utility function to emit Socket.IO events
def emit_socket_event(event_name, data):
    """
    Utility function to emit Socket.IO events.
    :param event_name: The name of the event to emit.
    :param data: Data to send along with the event.
    """
    socketio.emit(event_name, data)

@admin.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('auth.login'))

    # Fetch additional data for the dashboard
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    return render_template('admin/admin_dashboard.html',
                           total_users=total_users,
                           active_users=active_users)

@admin.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('auth.login'))

    pending_users = User.query.filter_by(status='pending').all()
    operatives = User.query.filter_by(role='operative').all()

    return render_template('admin/manage_users.html',
                           pending_users=pending_users,
                           operatives=operatives)

@admin.route('/orders', methods=['GET'])
@login_required
def orders():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('auth.login'))

    # Get filtering parameters from the URL
    company = request.args.get('company')
    sku = request.args.get('sku')
    order_status = request.args.get('order_status')
    eta = request.args.get('eta')
    cutoff_date = request.args.get('cutoff_date')
    sort_by = request.args.get('sort_by', 'eta')
    sort_order = request.args.get('sort_order', 'asc')

    # Build the query dynamically based on the provided filters
    query = Order.query

    if company:
        query = query.filter(Order.company.ilike(f"%{company}%"))
    if sku:
        query = query.filter(Order.sku.ilike(f"%{sku}%"))
    if order_status:
        query = query.filter(Order.order_status.ilike(f"%{order_status}%"))
    if eta:
        query = query.filter(Order.eta <= eta)
    if cutoff_date:
        query = query.filter(Order.cutoff_date <= cutoff_date)

    if sort_by:
        if sort_order == 'desc':
            query = query.order_by(db.desc(getattr(Order, sort_by)))
        else:
            query = query.order_by(getattr(Order, sort_by))

    # Fetch filtered orders from the database
    orders = query.all()

    return render_template('admin/orders.html', orders=orders)

@admin.route('/add_order', methods=['POST'])
@login_required
def add_order():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    # Get form data
    company = request.form.get('company')
    sku = request.form.get('sku')
    invoice_no = request.form.get('invoice_no')
    order_status = request.form.get('order_status')
    quantity = request.form.get('quantity')
    eta = request.form.get('eta')
    discrepancies = request.form.get('discrepancies')
    cutoff_date = request.form.get('cutoff_date')

    # Convert eta and cutoff_date to datetime objects
    try:
        eta = datetime.strptime(eta, '%Y-%m-%dT%H:%M')
        cutoff_date = datetime.strptime(cutoff_date, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format for ETA or Cutoff Date.', 'danger')
        return redirect(url_for('admin.orders'))

    # Handle discrepancies if empty
    if not discrepancies:
        discrepancies = None

    # Create new order object
    new_order = Order(
        company=company,
        sku=sku,
        invoice_no=invoice_no,
        order_status=order_status,
        quantity=int(quantity),
        eta=eta,
        discrepancies=discrepancies,
        cutoff_date=cutoff_date
    )

    try:
        # Add the new order to the database
        db.session.add(new_order)
        db.session.commit()
        flash('New order has been successfully placed!', 'success')
    except Exception as e:
        flash(f"An error occurred while placing the order: {e}", 'danger')
        print(f"Error: {e}")

    return redirect(url_for('admin.orders'))

@admin.route('/upload_orders', methods=['POST'])
@login_required
def upload_orders():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('admin.orders'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('admin.orders'))

    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Iterate over the DataFrame rows and add to the database
            for index, row in df.iterrows():
                discrepancies = row.get('Discrepancies (damaged or missing items)', None)

                if pd.isna(discrepancies):
                    discrepancies = None
                else:
                    discrepancies = str(discrepancies)

                new_order = Order(
                    company=row.get('Company', None),
                    sku=row['SKU'],
                    invoice_no=row['Invoice NO'],
                    order_status=row['Order Status'],
                    quantity=row['Quantity (units)'],
                    eta=pd.to_datetime(row['ETA']),
                    discrepancies=discrepancies,
                    cutoff_date=pd.to_datetime(row['Cutoff Date'])
                )
                db.session.add(new_order)

            db.session.commit()
            flash('Orders have been successfully uploaded and added to the database!', 'success')
        except Exception as e:
            flash(f"An error occurred while processing the file: {e}", 'danger')
            print(f"Error: {e}")
    else:
        flash('Invalid file type. Please upload a CSV or Excel file.', 'danger')

    return redirect(url_for('admin.orders'))

@admin.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.get_or_404(user_id)
    user.status = 'confirmed'
    user.is_active = True
    db.session.commit()
    flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/decline_user/<int:user_id>', methods=['POST'])
@login_required
def decline_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been declined and deleted.', 'danger')
    return redirect(url_for('admin.manage_users'))

@admin.route('/settings')
@login_required
def settings():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/admin_settings.html')

@admin.route('/assign_pick_order', methods=['GET', 'POST'])
@login_required
def assign_pick_order():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            data = request.get_json()  # Get JSON data from the AJAX request
            
            if data is None:
                raise ValueError("No JSON data received")
                
            # Extract data
            order_no = data.get('order_no')
            customer_name = data.get('customer_name')
            delivery_comment = data.get('delivery_comment')
            
            # Check if required data is present
            if not order_no or not customer_name or not delivery_comment:
                raise ValueError("Missing required fields: order_no, customer_name, or delivery_comment")

            # Create a new DailyOrder object
            new_daily_order = DailyOrder(
                order_no=order_no,
                customer_name=customer_name,
                delivery_comment=delivery_comment,
                date_assigned=datetime.utcnow(),
                status='pending'
            )

            # Add the new pick order to the database
            db.session.add(new_daily_order)
            db.session.commit()

            # Emit a Socket.IO event to update the operatives
            emit_socket_event('new_pick_order', {
                'id':new_daily_order.id,
                'order_no': new_daily_order.order_no,
                'customer_name': new_daily_order.customer_name,
                'delivery_comment': new_daily_order.delivery_comment,
                'status': new_daily_order.status
            })

            return jsonify({"success": True}), 200
        except ValueError as ve:
            print(f"ValueError: {ve}")
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            db.session.rollback()
            print(f"Unexpected error: {e}")
            return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

    daily_orders = DailyOrder.query.all()
    return render_template('admin/assign_pick_order.html', daily_orders=daily_orders)

@admin.route('/delete_order/<int:order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access!"}), 403

    try:
        # Find the order to delete
        order = DailyOrder.query.get_or_404(order_id)

        # Delete the order from the database
        db.session.delete(order)
        db.session.commit()

        # Emit a Socket.IO event to update the operatives about the deleted order
        emit_socket_event('delete_pick_order', {'id': order.id})

        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting order: {e}")
        return jsonify({"error": str(e)}), 500


@admin.route('/update_order/<int:order_id>', methods=['POST'])
@login_required
def update_order(order_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access!"}), 403

    try:
        data = request.get_json()
        if data is None:
            raise ValueError("No JSON data received")

        # Get the order from the database
        order = DailyOrder.query.get_or_404(order_id)

        # Prepare change description
        changes = []
        if 'order_no' in data and data['order_no'] != order.order_no:
            changes.append(f"Order number changed from {order.order_no} to {data['order_no']}")
            order.order_no = data['order_no']

        if 'customer_name' in data and data['customer_name'] != order.customer_name:
            changes.append(f"Customer name changed from {order.customer_name} to {data['customer_name']}")
            order.customer_name = data['customer_name']

        if 'delivery_comment' in data and data['delivery_comment'] != order.delivery_comment:
            changes.append(f"Delivery comment changed from {order.delivery_comment} to {data['delivery_comment']}")
            order.delivery_comment = data['delivery_comment']

        if not changes:
            return jsonify({"error": "No changes made"}), 400

        # Commit changes to the database
        db.session.commit()

        # Log the update in the DailyOrderUpdate table
        update_log = DailyOrderUpdate(
            daily_order_id=order.id,
            user_id=current_user.id,
            changes="; ".join(changes),
            timestamp=datetime.utcnow()
        )
        db.session.add(update_log)
        db.session.commit()

        # Emit a Socket.IO event to update the operatives
        emit_socket_event('update_pick_order', {
            'id': order.id,
            'order_no': order.order_no,
            'customer_name': order.customer_name,
            'delivery_comment': order.delivery_comment,
            'status': order.status
        })

        return jsonify({"success": True}), 200

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error updating order: {e}")
        return jsonify({"error": str(e)}), 500



@admin.route('/get_order/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access!"}), 403

    try:
        # Get the order details
        order = DailyOrder.query.get_or_404(order_id)
        return jsonify({"success": True, "order": {
            "order_no": order.order_no,
            "customer_name": order.customer_name,
            "delivery_comment": order.delivery_comment
        }}), 200
    except Exception as e:
        print(f"Error fetching order: {e}")
        return jsonify({"error": str(e)}), 500
