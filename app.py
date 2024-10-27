import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash, request
from models import db, Student, Room, Expense, Issue, Admin
from forms import EnrollForm, ExpenseForm, IssueForm, AdminLoginForm, AdminRegisterForm, StudentForm
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


@app.route('/enroll', methods=['GET', 'POST'])
@login_required
def enroll():
    form = StudentForm()
    if form.validate_on_submit():
        student = Student(
            name=form.name.data,
            student_id=form.student_id.data,
            age=form.age.data,
            contact_number=form.contact_number.data,
            email=form.email.data,
            address=form.address.data,
            room_id=form.room_number.data,
            admission_date=form.admission_date.data
        )
        db.session.add(student)
        db.session.commit()
        flash('Student enrolled successfully', 'success')
        return redirect(url_for('students'))
    return render_template('enroll.html', form=form)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    return render_template('expenses.html')

# Student Registration
@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    search = request.args.get('search')
    if search:
        all_students = Student.query.filter(Student.name.contains(search) | Student.student_id.contains(search)).all()
    else:
        all_students = Student.query.all()
    return render_template('students.html', students=all_students)

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
