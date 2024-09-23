from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from werkzeug.security import check_password_hash
from app import db, mail

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

        # Check if the user exists and if the password is correct
        if user and user.check_password(password):
            login_user(user)  # Logs the user in

            # Redirect based on the user's role after successful login
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))  # Admin dashboard
            elif user.role == 'operative':
                return redirect(url_for('main.operative_dashboard'))  # Operative dashboard
            else:
                return redirect(url_for('main.home'))

        flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html')

# Registration route
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # Get the selected role

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(username=username, email=email, role=role)  # Save the role in the database
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
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
    return render_template('admin_dashboard.html')

# Operative Dashboard route
@main.route('/operative_dashboard')
@login_required
def operative_dashboard():
    if current_user.role != 'operative':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.home'))
    return render_template('operative_dashboard.html')

#log out route
@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))
