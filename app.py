import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash, request
from models import db, Student, Room, Expense, Issue, Admin

from datetime import datetime

from forms import EnrollForm, ExpenseForm, IssueForm, AdminLoginForm,AdminRegisterForm
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# After initializing db
migrate = Migrate(app, db)

def create_tables():
    db.create_all()
    for i in range(1, 9):
        if not Room.query.filter_by(room_number=i).first():
            room = Room(room_number=i)
            db.session.add(room)
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('Home.html')

# Student Login
@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and bcrypt.check_password_hash(admin.password_hash, form.password.data):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('admin_login.html', form=form)

# Admin Dashboard
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Room Management (Admin Only)
@app.route('/room_management')
@login_required
def room_management():
    return render_template('room_management.html')

# Add this function at the beginning of app.py
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/enroll', methods=['GET', 'POST'])
@login_required
def enroll():
    form = EnrollForm()
    if form.validate_on_submit():
        # Check if the file is present and allowed
        if 'picture' not in request.files:
            flash('No picture file provided', 'danger')
            return redirect(request.url)

        picture = request.files['picture']
        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)

            # Create a new student object
            student = Student(
                name=form.name.data,
                fee=form.fee.data,
                room_id=form.room_number.data,
                picture=filename  # Store filename in the database
            )

            # Add student to the database
            try:
                db.session.add(student)
                db.session.commit()
                flash('Student enrolled successfully!', 'success')
                return redirect(url_for('students'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error enrolling student: {e}', 'danger')
        else:
            flash('Invalid file format. Allowed types are png, jpg, jpeg, gif.', 'danger')
            
    return render_template('enroll.html', form=form)

# @app.route('/expenses', methods=['GET', 'POST'])
# def expenses():
#     form = ExpenseForm()
#     if form.validate_on_submit():
#         # Save the new expense to the database
#         new_expense = Expense(
#             item_name=form.item_name.data,
#             price=form.price.data,
#             date=form.date.data
#         )
#         db.session.add(new_expense)
#         db.session.commit()
#         flash('Expense added successfully!', 'success')
#         return redirect(url_for('expenses'))
    
#     # Retrieve all expenses from the database
#     expenses = Expense.query.all()
#     total = sum(expense.price for expense in expenses)
    
#     return render_template('expenses.html', form=form, expenses=expenses, total=total)

@app.route('/expenses', methods=['GET', 'POST'])
@app.route('/expenses/<int:year>/<int:month>', methods=['GET', 'POST'])
def expenses(year=None, month=None):
    form = ExpenseForm()
    
    # Add new expense if form is submitted
    if form.validate_on_submit():
        new_expense = Expense(
            item_name=form.item_name.data,
            price=form.price.data,
            date=form.date.data
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))
    
    # If year and month are provided, filter expenses for that month
    if year and month:
        expenses = Expense.query.filter(
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == month
        ).all()
    else:
        # Default to current month if no year/month is provided
        today = datetime.today()
        expenses = Expense.query.filter(
            db.extract('year', Expense.date) == today.year,
            db.extract('month', Expense.date) == today.month
        ).all()
    
    # Calculate total expenses for the selected month
    total = sum(expense.price for expense in expenses)
    
    return render_template('expenses.html', form=form, expenses=expenses, total=total, year=year, month=month)
@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/students')
@login_required
def students():
    page = request.args.get('page', 1, type=int)  # Get current page number, default is 1
    per_page = 10  # Number of students per page
    paginated_students = Student.query.paginate(page=page, per_page=per_page)
    return render_template('students.html', students=paginated_students)


@app.route('/rooms')
@login_required
def rooms():
    all_rooms = Room.query.all()
    return render_template('rooms.html', rooms=all_rooms)

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    form = AdminRegisterForm()
    if form.validate_on_submit():
        existing_admin = Admin.query.filter_by(email=form.email.data).first()
        if existing_admin:
            flash('Email already in use', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_admin = Admin(name=form.name.data, username=form.name.data, email=form.email.data, password_hash=hashed_password)
            try:
                db.session.add(new_admin)
                db.session.commit()
                flash('Admin registered successfully', 'success')
                return redirect(url_for('admin_login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error registering admin: {e}', 'danger')
    return render_template('admin_register.html', form=form)

if __name__ == '__main__':
    app.run(debug=True,port=5051)
