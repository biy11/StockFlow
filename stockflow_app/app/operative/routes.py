# app/operative/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash,  jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db, socketio
# Import your Order model if needed
from app.models import DailyOrder, DailyOrderUpdate, CompletedOutgoingOrder

# Define the Blueprint here
operative = Blueprint('operative', __name__, template_folder='templates')

@operative.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'operative':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('operative/operative_dashboard.html')

@operative.route('/daily_orders')
@login_required
def daily_orders():
    if current_user.role != 'operative':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    # Replace with actual logic to retrieve daily orders
    daily_orders = DailyOrder.query.all()  # e.g., Order.query.filter_by(...).all()

    return render_template('operative/operative_orders.html', daily_orders=daily_orders)


@operative.route('/process_order/<int:order_id>', methods=['POST'])
@login_required
def process_order(order_id):
    if current_user.role != 'operative':
        return jsonify({"error": "Unauthorized access!"}), 403

    order = DailyOrder.query.get_or_404(order_id)
    if order.status == 'pending':
        order.status = 'in process'
        db.session.commit()
        # Emit event to inform other clients about the status update
        socketio.emit('update_pick_order', {
            'id': order.id,
            'order_no': order.order_no,
            'customer_name': order.customer_name,
            'delivery_comment': order.delivery_comment,
            'status': order.status,
        })
    else:
        return jsonify({"error": "Invalid order status transition!"}), 400

    return jsonify({"success": True, "order": {
        "id": order_id,
        "status": order.status
    }}), 200



@operative.route('/raise_inquiry/<int:order_id>', methods=['POST'])
@login_required
def raise_inquiry(order_id):
    if current_user.role != 'operative':
        return jsonify({"error": "Unauthorized access!"}), 403

    order = DailyOrder.query.get_or_404(order_id)
    inquiry_comment = request.json.get('comment', '')

    if not inquiry_comment:
        return jsonify({"error": "Inquiry comment is required"}), 400

    order.status = 'inquiry raised'

    # Log the inquiry in DailyOrderUpdate table
    update_log = DailyOrderUpdate(
        daily_order_id=order.id,
        user_id=current_user.id,
        changes=f"Inquiry raised: {inquiry_comment}",
        timestamp=datetime.utcnow()
    )
    db.session.add(update_log)
    db.session.commit()

    return jsonify({"success": True, "order": {
        "id": order.id,
        "status": order.status
    }}), 200

@operative.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.role != 'operative':
        return jsonify({"error": "Unauthorized access!"}), 403

    try:
        data = request.get_json()
        action = data.get('action')

        order = DailyOrder.query.get_or_404(order_id)

        if action == 'process':
            order.status = 'in process'
        elif action == 'confirm_complete':
            order.status = 'confirmed'
            # Move to completed orders table (implement separately)
            # db.session.add(CompletedOutgoingOrder(...))
            db.session.delete(order)  # remove from daily orders
        elif action == 'raise_inquiry':
            inquiry_comment = data.get('inquiry_comment', '')
            order.status = 'inquiry raised'
            # You may want to save the inquiry comment somewhere, e.g., DailyOrderUpdate

        db.session.commit()

        # Emit Socket.IO event to inform operatives/admins of the status update
        emit_socket_event('update_pick_order', {
            'id': order.id,
            'status': order.status
        })

        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@operative.route('/confirm_order_complete/<int:order_id>', methods=['POST'])
@login_required
def confirm_order_complete(order_id):
    if current_user.role != 'operative':
        return jsonify({"error": "Unauthorized access!"}), 403

    order = DailyOrder.query.get_or_404(order_id)
    if order.status == 'in process':
        # Move the order to CompletedOutgoingOrder
        completed_order = CompletedOutgoingOrder(
            order_no=order.order_no,
            customer_name=order.customer_name,
            delivery_comment=order.delivery_comment,
            completion_date=datetime.utcnow(),
            operative_id=current_user.id
        )
        db.session.add(completed_order)
        db.session.delete(order)  # Remove from DailyOrder
        db.session.commit()
        # Emit event to inform other clients that the order has been removed
        socketio.emit('delete_pick_order', {'id': order_id})
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Invalid order status transition!"}), 400
