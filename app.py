from flask import Flask, render_template, redirect, url_for, flash
from models import db, Student, Room , Expense
from forms import EnrollForm
from forms import ExpenseForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel.db'
db.init_app(app)

@app.before_request

def create_tables():
    app.before_request_funcs[None].remove(create_tables)
    db.create_all()
    for i in range(1, 9):
        if not Room.query.filter_by(room_number=i).first():
            room = Room(room_number=i)
            db.session.add(room)
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    form = EnrollForm()
    if form.validate_on_submit():
        room = Room.query.filter_by(room_number=form.room_number.data).first()
        if room and len(room.students) < 4:
            student = Student(name=form.name.data, room=room)
            db.session.add(student)
            db.session.commit()
            flash('Student enrolled successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Room is full or does not exist', 'danger')
    return render_template('enroll.html', form=form)

@app.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('students.html', students=all_students)

@app.route('/rooms')
def rooms():
    all_rooms = Room.query.all()
    return render_template('rooms.html', rooms=all_rooms)

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(item_name=form.item_name.data, price=form.price.data)
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully', 'success')
        return redirect(url_for('expenses'))
    
    all_expenses = Expense.query.all()
    total_expense = sum(expense.price for expense in all_expenses)
    return render_template('expenses.html', form=form, expenses=all_expenses, total=total_expense)


if __name__ == '__main__':
    app.run(debug=True)
