import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash
from models import db, Student, Room, Expense, Issue
from forms import EnrollForm, ExpenseForm, IssueForm
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)

# After initializing db
migrate = Migrate(app, db)

def create_tables():
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
        # Handle picture upload
        picture_file = form.picture.data
        filename = secure_filename(picture_file.filename)
        picture_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Create a new student
        room = Room.query.filter_by(room_number=form.room_number.data).first()
        if room and len(room.students) < 4:
            student = Student(name=form.name.data, fee=form.fee.data, picture=filename, room=room)
            try:
                db.session.add(student)
                db.session.commit()
                flash('Student enrolled successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error enrolling student: {e}', 'danger')
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
        try:
            db.session.add(expense)
            db.session.commit()
            flash('Expense added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding expense: {e}', 'danger')
        return redirect(url_for('expenses'))

    all_expenses = Expense.query.all()
    total_expense = sum(expense.price for expense in all_expenses)
    return render_template('expenses.html', form=form, expenses=all_expenses, total=total_expense)

@app.route('/issues', methods=['GET', 'POST'])
def issues():
    form = IssueForm()
    if form.validate_on_submit():
        issue = Issue(title=form.title.data, description=form.description.data, status=form.status.data)
        try:
            db.session.add(issue)
            db.session.commit()
            flash('Issue added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding issue: {e}', 'danger')
        return redirect(url_for('issues'))

    all_issues = Issue.query.all()
    return render_template('issues.html', form=form, issues=all_issues)

if __name__ == '__main__':
    app.run(debug=True)
