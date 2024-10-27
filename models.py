from flask_sqlalchemy import SQLAlchemy
from datetime import datetime  # Added to use datetime for the date column
from flask_login import UserMixin

db = SQLAlchemy()

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    students = db.relationship('Student', backref='room', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fee = db.Column(db.Float, nullable=False, server_default='0')
    picture = db.Column(db.String(100), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Date column added as per plan

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)  # Retain username from the add-admin-login branch
    name = db.Column(db.String(100), nullable=False)  # Retain name from the master branch
    email = db.Column(db.String(100), unique=True, nullable=False)  # Retain email from the master branch
    password_hash = db.Column(db.String(128), nullable=False)  # Use password_hash from add-admin-login

