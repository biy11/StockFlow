# routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from app.models import User
from werkzeug.security import check_password_hash
from app import db
from datetime import datetime


main = Blueprint('main', __name__)

# Home route (redirect based on role if logged in)
@main.route('/')
@login_required
def home():
    # Redirect based on the user's role
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'operative':
        return redirect(url_for('main.operative_dashboard'))
    return render_template('home.html')

# Login route
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find the user in the database
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.status == 'pending':
                flash('Your account is awaiting admin approval.', 'warning')
                return redirect(url_for('main.login'))
            elif user.is_active:
                login_user(user)  # Logs the user in
                user.last_login = datetime.utcnow()
                user.is_logged_in = True  # Mark as logged in
                db.session.commit()

                # Redirect based on the user's role
                if user.role == 'admin':
                    return redirect(url_for('main.admin_dashboard'))
                elif user.role == 'operative':
                    return redirect(url_for('main.operative_dashboard'))
                else:
                    return redirect(url_for('main.home'))

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
        role = request.form['role']  # Get the selected role

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
            new_user.is_active = False  # Inactive until admin approval
            db.session.add(new_user)
            db.session.commit()

            flash('Registration request submitted! Await admin approval.', 'success')
            return redirect(url_for('main.login'))

        flash('Email already registered.', 'danger')

    return render_template('register.html')

# Admin Dashboard route
@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))

    # Fetch all pending user registrations (status is 'pending')
    pending_users = User.query.filter_by(status='pending').all()

    # Fetch all operatives (role is 'operative')
    operatives = User.query.filter_by(role='operative').all()

    # Calculate total and active users for the overview
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    return render_template('admin_dashboard.html', 
                           pending_users=pending_users, 
                           operatives=operatives, 
                           total_users=total_users, 
                           active_users=active_users)

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
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))

    # Fetch all pending user registrations
    pending_users = User.query.filter_by(is_active=False).all()
    return render_template('manage_users.html', users=pending_users)

# Routes to approve or decline user registration
@main.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))

    user = User.query.get_or_404(user_id)
    user.status = 'confirmed'  # Update status to 'confirmed'
    user.is_active = True  # Activate account on approval
    db.session.commit()
    flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/decline_user/<int:user_id>', methods=['POST'])
@login_required
def decline_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
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
    current_user.is_logged_in = False  # Mark as logged out
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))