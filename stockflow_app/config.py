import os

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = os.getenv('MAIL_USERNAME') 
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  
MAIL_DEFAULT_SENDER = 'bilalyousufzai28@gmail.com'
SECRET_KEY = 'your_secret_key'  # Replace with your secret key
SECURITY_PASSWORD_SALT = 'your_security_password_salt'  # Replace with a security salt

# Add the SQLAlchemy database URI
SQLALCHEMY_DATABASE_URI = 'postgresql://stockflow_user:cuCxab-dotgug-runte7@localhost/stockflow_db'
