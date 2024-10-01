# app/operative/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
# Import your Order model if needed
from app.models import DailyOrder

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
