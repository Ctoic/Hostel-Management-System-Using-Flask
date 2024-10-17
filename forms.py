from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, NumberRange
from wtforms import StringField, FloatField, SubmitField, FileField , IntegerField, DateField  # DateField imported
from wtforms.validators import DataRequired
from flask_wtf.file import FileRequired, FileAllowed


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
