# app/auth/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from app.models import User
from app import db
from app.utils import generate_verification_token, confirm_verification_token, send_email
from flask import session
import os

# Define the Blueprint here
auth = Blueprint('auth', __name__, template_folder='templates')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Registration logic
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # Create a new user with 'pending' status
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            role=role,
            status='pending',
            is_active=False
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Generate token and send verification email
        token = generate_verification_token(email)
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        html = render_template('auth/verify_email.html', verify_url=verify_url)
        subject = "Please confirm your email"
        send_email(email, subject, html)

        flash('A verification email has been sent to your email address. Please verify to activate your account.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth.route('/verify/<token>')
def verify_email(token):
    try:
        email = confirm_verification_token(token)
    except:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_active:
        flash('Account already verified. Please login.', 'success')
    else:
        # Email is verified, but admin approval is still needed
        user.is_active = True
        user.status = 'pending'  # Keep the status as pending for admin approval
        db.session.commit()
        flash('Your email has been verified! However, your account is awaiting admin approval.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Login logic
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.status == 'pending':
                flash('Your account has been verified but is still awaiting admin approval.', 'warning')
                return redirect(url_for('auth.login'))
            elif user.is_active:
                login_user(user)
                user.last_login = datetime.utcnow()
                user.is_logged_in = True
                db.session.commit()

                # Set the session as permanent (to allow auto logout on timeout)
                session.permanent = True
                # Define the session timeout duration (30 minutes as an example)
                current_app.permanent_session_lifetime = os.getenv('SESSION_TIMEOUT', 1800)

                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'operative':
                    return redirect(url_for('operative.dashboard'))

        flash('Login failed. Check your email and password.', 'danger')

    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    # Mark the user as logged out
    current_user.is_logged_in = False
    db.session.commit()

    # Clear the session
    session.clear()

    # Log the user out of Flask-Login
    logout_user()

    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
