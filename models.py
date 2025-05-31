from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship


db = SQLAlchemy()

# FeeRecord Model
class FeeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date_paid = db.Column(db.Date, default=datetime.utcnow)
    student = relationship('Student', back_populates='fee_records')


# Room Model
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    students = relationship('Student', back_populates='room')

# Student Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fee = db.Column(db.Float, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    picture = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, inactive, graduated
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_fee_payment = db.Column(db.DateTime)
    
    # Relationships
    room = relationship('Room', back_populates='students')
    fee_records = relationship('FeeRecord', back_populates='student')

    def __repr__(self):
        return f'<Student {self.name}>'

    @property
    def is_fee_paid(self):
        """Check if the student has paid fees for the current month"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        return FeeRecord.query.filter(
            FeeRecord.student_id == self.id,
            db.extract('month', FeeRecord.date_paid) == current_month,
            db.extract('year', FeeRecord.date_paid) == current_year
        ).first() is not None

    @property
    def fee_status(self):
        """Get the fee payment status for the current month"""
        if not self.is_fee_paid:
            return 'unpaid'
        return 'paid'

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # DateTime for precise date
    user_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)  # Foreign key to Admin
    user = relationship('Admin', backref='expenses')  # Relationship with Admin model
    
    def __repr__(self):
        return f"<Expense {self.item_name} {self.price}>"

# Issue Model
class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Admin Model (UserMixin provides useful methods like is_authenticated)
class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)