from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_cors import CORS
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO()  # Initialize globally
migrate = Migrate()  # Initialize Flask-Migrate

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object('config.Config')

    # Enable CORS
    CORS(app, resources={r"/socket.io/*":{"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate with app and db
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)  # Bind socketio to the app

    # Import and register Blueprints
    from app.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import admin as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.operative import operative as operative_bp
    app.register_blueprint(operative_bp, url_prefix='/operative')

    # Redirect home to login if not authenticated
    @app.route('/')
    def home():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'operative':
                return redirect(url_for('operative.dashboard'))
        return redirect(url_for('auth.login'))

    # User loader callback
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    return app

app = create_app()
