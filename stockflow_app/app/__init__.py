# app/__init__.py
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_mail import Mail
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Import and register Blueprints
    from app.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import admin as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.operative import operative as operative_bp
    app.register_blueprint(operative_bp, url_prefix='/operative')

    # Home route
    @app.route('/')
    @login_required
    def home():
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'operative':
            return redirect(url_for('operative.dashboard'))
        return render_template('home.html')

    # User loader callback
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

app = create_app()
