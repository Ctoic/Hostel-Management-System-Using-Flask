from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, NumberRange, Email, Length, Regexp
from wtforms import StringField, FloatField, SubmitField, FileField , IntegerField, DateField, PasswordField  # DateField imported
from flask_wtf.file import FileRequired, FileAllowed


# forms.py
class FeeCollectionForm(FlaskForm):
    student_id = IntegerField('Student ID', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Payment')



class EnrollForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    fee = FloatField('Fee', validators=[DataRequired(), NumberRange(min=0)])
    room_number = IntegerField('Room Number', validators=[DataRequired(), NumberRange(min=1, max=8)])
    picture = FileField('Picture', validators=[DataRequired()])
    submit = SubmitField('Enroll')

class ExpenseForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    date = DateField('Date', validators=[DataRequired()])  # DateField added to ExpenseForm
    submit = SubmitField('Add Expense')

class IssueForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    status = StringField('Status', validators=[DataRequired()])
    submit = SubmitField('Add Issue')

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AdminRegisterForm(FlaskForm):
    name = StringField('Name', default='test', validators=[DataRequired()])
    email = StringField('Email', default='test@mail.com', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp('^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}$',
         message='Password must contain at least one letter and one number')
    ])
    submit = SubmitField('Register')

