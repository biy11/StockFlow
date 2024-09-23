from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate  # Add this import

mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Add this

def create_app():
    app = Flask(__name__)

    # Load config from config.py
    app.config.from_pyfile('../config.py')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)  # Add this line

    # Set login view if a user tries to access a protected route
    login_manager.login_view = 'main.login'

    # Define user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)

    return app
