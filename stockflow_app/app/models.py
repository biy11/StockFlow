# models.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from . import db

# models.py
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)  # Add first name
    last_name = db.Column(db.String(50), nullable=False)   # Add last name
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default='operative')
    status = db.Column(db.String(20), nullable=False, default='pending')
    last_login = db.Column(db.DateTime, nullable=True)
    is_logged_in = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), nullable=False)
    invoice_no = db.Column(db.String(50), nullable=False)
    order_status = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    eta = db.Column(db.DateTime, nullable=False)
    discrepancies = db.Column(db.String(255), nullable=True) 
    cutoff_date = db.Column(db.DateTime, nullable=False)
    company = db.Column(db.String(100), nullable=True)

class DailyOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    delivery_comment = db.Column(db.String(255), nullable=True)
    date_assigned = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'in process', 'inquiry raised', 'completed'

    updates = db.relationship('DailyOrderUpdate', backref='daily_order', lazy=True, cascade='all, delete-orphan')

# DailyOrderUpdate model to track changes
class DailyOrderUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daily_order_id = db.Column(db.Integer, db.ForeignKey('daily_order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    changes = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    #daily_order = db.relationship('DailyOrder', backref=db.backref('updates', lazy=True))
    user = db.relationship('User', backref=db.backref('updates', lazy=True))

class CompletedOutgoingOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    delivery_comment = db.Column(db.String(255), nullable=True)
    completion_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    operative_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    operative = db.relationship('User', backref=db.backref('completed_orders', lazy=True))
