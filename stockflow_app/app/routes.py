# routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, Order  # Assuming you have an Order model
from app import db
from datetime import datetime
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
import pandas as pd  # For CSV/Excel file processing
import os

mail = Mail()

main = Blueprint('main', __name__)

# Function to generate token
def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

# Function to verify token
def confirm_verification_token(token, expiration=3600):  # 1 hour expiration
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return email

# Route to handle registration
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('main.register'))

        # Create a new user with 'pending' status
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            role=role,
            status='pending',  # Assuming you have a 'status' field
            is_active=False  # Inactive until email is confirmed
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Generate token and send verification email
        token = generate_verification_token(email)
        verify_url = url_for('main.verify_email', token=token, _external=True)
        html = render_template('verify_email.html', verify_url=verify_url)
        subject = "Please confirm your email"
        send_email(email, subject, html)

        flash('A verification email has been sent to your email address. Please verify to activate your account.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')

# Route to verify email
@main.route('/verify/<token>')
def verify_email(token):
    try:
        email = confirm_verification_token(token)
    except:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('main.login'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_active:
        flash('Account already verified. Please login.', 'success')
    else:
        user.is_active = True
        user.status = 'confirmed'  # Update the status to 'confirmed'
        db.session.commit()
        flash('Your account has been verified! You can now log in.', 'success')
    return redirect(url_for('main.login'))

# Utility function to send emails
def send_email(to, subject, template):
    msg = Message(subject, recipients=[to], html=template, sender=current_app.config['MAIL_DEFAULT_SENDER'])
    mail.send(msg)

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
@main.route('/admin_dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    # Fetch additional data for the dashboard
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           active_users=active_users)

# Orders route
@main.route('/orders', methods=['GET'])
@login_required
def orders():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    # Get filtering parameters from the URL
    company = request.args.get('company')
    sku = request.args.get('sku')
    order_status = request.args.get('order_status')
    eta = request.args.get('eta')
    cutoff_date = request.args.get('cutoff_date')

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

    # Fetch filtered orders from the database
    orders = query.all()

    return render_template('orders.html', orders=orders)

# Add Order route
@main.route('/add_order', methods=['POST'])
@login_required
def add_order():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))

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
        return redirect(url_for('main.orders'))

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
        print(f"Error: {e}")  # Debugging: print the exception for clarity

    return redirect(url_for('main.orders'))

# Upload Orders route
@main.route('/upload_orders', methods=['POST'])
@login_required
def upload_orders():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))

    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('main.orders'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('main.orders'))

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
                    discrepancies = None  # Set to None if it's NaN
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
            print(f"Error: {e}")  # Debugging: print the exception for clarity
    else:
        flash('Invalid file type. Please upload a CSV or Excel file.', 'danger')

    return redirect(url_for('main.orders'))

# Manage Users route for admin
@main.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Unauthorized access! Admins only.', 'danger')
        return redirect(url_for('main.home'))

    pending_users = User.query.filter_by(status='pending').all()
    operatives = User.query.filter_by(role='operative').all()

    return render_template('manage_users.html',
                           pending_users=pending_users,
                           operatives=operatives)

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
    return redirect(url_for('main.manage_users'))

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
    return redirect(url_for('main.manage_users'))

# Settings route
@main.route('/settings')
@login_required
def settings():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))
    return render_template('admin_settings.html')

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

# Operative Dashboard route
@main.route('/operative_dashboard')
@login_required
def operative_dashboard():
    if current_user.role != 'operative':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))
    return render_template('operative_dashboard.html')

# Add any additional routes as needed
