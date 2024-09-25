import os

class Config:
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = 'bilalyousufzai28@gmail.com'
    SECRET_KEY = 'your_secret_key'  # Replace with your secret key
    SECURITY_PASSWORD_SALT = 'your_security_password_salt'  # Replace with a security salt

    # Use environment variables to choose the database user dynamically
    DB_USER = os.getenv('DB_USER', 'stockflow_user')  # Default to stockflow_user
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'cuCxab-dotgug-runte7')  # Default password for stockflow_user
    DB_NAME = os.getenv('DB_NAME', 'stockflow')
    DB_HOST = os.getenv('DB_HOST', 'localhost')

    # Add the SQLAlchemy database URI
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

