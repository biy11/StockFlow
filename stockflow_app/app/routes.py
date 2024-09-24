from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, Order  # Assuming you have an Order model
from app import db
from datetime import datetime
import pandas as pd  # For CSV/Excel file processing
import os

main = Blueprint('main', __name__)

# Home route (redirect based on role if logged in)
@main.route('/')
@login_required
def home():
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'operative':
        return redirect(url_for('main.operative_dashboard'))
    return render_template('home.html')

# Admin Dashboard route (only accessible to admin)
@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    # Fetch pending users and operatives
    pending_users = User.query.filter_by(status='pending').all()
    operatives = User.query.filter_by(role='operative').all()
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    # Fetch all orders from the database
    orders = Order.query.all()

    return render_template('admin_dashboard.html',
                           pending_users=pending_users,
                           operatives=operatives,
                           total_users=total_users,
                           active_users=active_users,
                           orders=orders) 

@main.route('/upload_orders', methods=['POST'])
@login_required
def upload_orders():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))

    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Iterate over the DataFrame rows and add to the database
            for index, row in df.iterrows():
                discrepancies = row['Discrepancies (damaged or missing items)']
                
                if pd.isna(discrepancies):
                    discrepancies = None  # Set to None if it's NaN
                else:
                    discrepancies = str(discrepancies)

                new_order = Order(
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
            print(f"Error: {e}")  # Debugging: print the exception for clarity
    else:
        flash('Invalid file type. Please upload a CSV or Excel file.', 'danger')

    return redirect(url_for('main.admin_dashboard'))


# Operative Dashboard route
@main.route('/operative_dashboard')
@login_required
def operative_dashboard():
    if current_user.role != 'operative':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))
    return render_template('operative_dashboard.html')

# Manage Users route for admin
@main.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    pending_users = User.query.filter_by(is_active=False).all()
    return render_template('manage_users.html', users=pending_users)

# Routes to approve or decline user registration (Admin only)
@main.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    user = User.query.get_or_404(user_id)
    user.status = 'confirmed'
    user.is_active = True
    db.session.commit()
    flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/decline_user/<int:user_id>', methods=['POST'])
@login_required
def decline_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been declined and deleted.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

# Logout route
@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    current_user.is_logged_in = False
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))

# Login route
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.status == 'pending':
                flash('Your account is awaiting admin approval.', 'warning')
                return redirect(url_for('main.login'))
            elif user.is_active:
                login_user(user)  # Logs the user in
                user.last_login = datetime.utcnow()
                user.is_logged_in = True
                db.session.commit()

                if user.role == 'admin':
                    return redirect(url_for('main.admin_dashboard'))
                elif user.role == 'operative':
                    return redirect(url_for('main.operative_dashboard'))

        flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html')

# Registration route
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # Admin or Operative

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                role=role
            )
            new_user.set_password(password)
            new_user.is_active = False  # Await admin approval
            db.session.add(new_user)
            db.session.commit()

            flash('Registration request submitted! Await admin approval.', 'success')
            return redirect(url_for('main.login'))

        flash('Email already registered.', 'danger')

    return render_template('register.html')

# Route to display all orders (Admin only)
@main.route('/orders')
@login_required
def view_orders():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    # Query all orders from the database
    orders = Order.query.all()

    # Pass the orders to the template to be displayed
    return render_template('admin_dashboard.html', orders=orders)
