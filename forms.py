from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class EnrollForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    room_number = IntegerField('Room Number', validators=[DataRequired(), NumberRange(min=1, max=8)])
    submit = SubmitField('Enroll')
    
class ExpenseForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField(label='Add Expense')
    
    
