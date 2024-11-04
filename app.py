import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash, request
from models import db, Student, Room, Expense, Issue, Admin, FeeRecord
from datetime import datetime
from forms import EnrollForm, ExpenseForm, IssueForm, AdminLoginForm,AdminRegisterForm , FeeCollectionForm
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas



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
def expenses():
    form = ExpenseForm()
    current_year = datetime.today().year
    current_month = datetime.today().month

    # Adding a new expense if the form is submitted
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

    # Group expenses by month and year
    grouped_expenses = db.session.query(
        db.extract('year', Expense.date).label('year'),
        db.extract('month', Expense.date).label('month'),
        db.func.sum(Expense.price).label('total')
    ).group_by('year', 'month').order_by('year', 'month').all()

    # Retrieve expenses for a specific month if selected
    year = request.args.get('year', current_year, type=int)
    month = request.args.get('month', current_month, type=int)
    expenses = Expense.query.filter(
        db.extract('year', Expense.date) == year,
        db.extract('month', Expense.date) == month
    ).all()
    total = sum(expense.price for expense in expenses)

    return render_template('expenses.html', form=form, expenses=expenses, total=total,
                           grouped_expenses=grouped_expenses, year=year, month=month,
                           current_year=current_year, current_month=current_month)
# @app.route('/export_pdf/<int:year>/<int:month>', methods=['GET'])
# def export_pdf(year, month):
#     # Get expenses for the specified month and year
#     expenses = Expense.query.filter(
#         db.extract('year', Expense.date) == year,
#         db.extract('month', Expense.date) == month
#     ).all()

#     # Calculate total expenses for the month
#     total = sum(expense.price for expense in expenses)

#     # Create a BytesIO buffer for the PDF
#     buffer = BytesIO()
#     pdf = canvas.Canvas(buffer, pagesize=A4)
#     width, height = A4

#     # PDF Title
#     pdf.setFont("Helvetica-Bold", 16)
#     pdf.drawString(200, height - 50, f"Expense Report - {month}/{year}")

#     # Table headers
#     pdf.setFont("Helvetica-Bold", 12)
#     pdf.drawString(50, height - 100, "Item Name")
#     pdf.drawString(250, height - 100, "Price (Rs)")
#     pdf.drawString(400, height - 100, "Date")

#     # Table content
#     y_position = height - 130
#     pdf.setFont("Helvetica", 10)
#     for expense in expenses:
#         pdf.drawString(50, y_position, expense.item_name)
#         pdf.drawString(250, y_position, f"Rs {expense.price}")
#         pdf.drawString(400, y_position, expense.date.strftime('%Y-%m-%d'))
#         y_position -= 20

#         # Add a new page if y_position is too low
#         if y_position < 50:
#             pdf.showPage()
#             y_position = height - 50

#     # Total expenses
#     pdf.setFont("Helvetica-Bold", 12)
#     pdf.drawString(50, y_position - 30, f"Total Expenses for {month}/{year}: Rs {total}")

#     pdf.save()

#     # Move the buffer's position back to the start
#     buffer.seek(0)
    
#     # Send the PDF as a file download
#     return send_file(buffer, as_attachment=True, download_name=f"Expense_Report_{month}_{year}.pdf", mimetype='application/pdf')


# Constants
INCOME = 345000

@app.route('/export_pdf/<int:year>/<int:month>', methods=['GET'])
def export_pdf(year, month):
    # Get expenses for the specified month and year
    expenses = Expense.query.filter(
        db.extract('year', Expense.date) == year,
        db.extract('month', Expense.date) == month
    ).all()

    # Calculate total expenses for the month
    total_expenses = sum(expense.price for expense in expenses)
    remaining_balance = INCOME - total_expenses

    # Create a BytesIO buffer for the PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title section
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, height - 50, f"Monthly Expense Report - {month}/{year}")

    # Income and Expense Summary
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 100, f"Total Income: Rs {INCOME}")
    pdf.drawString(50, height - 120, f"Total Expenses: Rs {total_expenses}")
    if total_expenses > INCOME:
        pdf.drawString(50, height - 140, f"Additional Amount by Donors: Rs {total_expenses - INCOME}")

    # Table headers
    y_position = height - 180
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y_position, "Item Name")
    pdf.drawString(250, y_position, "Price (Rs)")
    pdf.drawString(400, y_position, "Date")

    # Table content
    pdf.setFont("Helvetica", 10)
    y_position -= 20
    for expense in expenses:
        pdf.drawString(50, y_position, expense.item_name)
        pdf.drawString(250, y_position, f"Rs {expense.price}")
        pdf.drawString(400, y_position, expense.date.strftime('%Y-%m-%d'))
        y_position -= 20
        if y_position < 50:
            pdf.showPage()
            y_position = height - 50

    # Total summary section
    y_position -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y_position, f"Total Expenses for {month}/{year}: Rs {total_expenses}")
    y_position -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y_position, f"Remaining Balance: Rs {remaining_balance if remaining_balance >= 0 else 0}")

    # Footer
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 30, "Report Generated By: Najam Ali")
    pdf.drawString(400, 30, "Report Approved By: Mr Bilal")

    pdf.save()
    buffer.seek(0)
    
    # Send the PDF as a file download
    return send_file(buffer, as_attachment=True, download_name=f"Expense_Report_{month}_{year}.pdf", mimetype='application/pdf')

# Edit expense route
@app.route('/edit_expense/<int:expense_id>', methods=['POST'])
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    expense.item_name = request.form['item_name']
    expense.price = float(request.form['price'])
    expense.date = request.form['date']
    
    db.session.commit()
    flash('Expense updated successfully!', 'success')
    return redirect(url_for('expenses', year=expense.date.year, month=expense.date.month))

# Delete expense route
@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses'))

# @app.route('/register')
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

# app.py
@app.route('/collect_fee', methods=['GET', 'POST'])
@login_required
def collect_fee():
    form = FeeCollectionForm()
    if form.validate_on_submit():
        student_id = form.student_id.data
        amount = form.amount.data
        student = Student.query.get(student_id)

        if student:
            fee_record = FeeRecord(student_id=student_id, amount=amount)
            db.session.add(fee_record)
            db.session.commit()
            flash('Fee payment recorded successfully!', 'success')
            return redirect(url_for('view_fee_records', student_id=student_id))
        else:
            flash('Student not found', 'danger')

    return render_template('collect_fee.html', form=form)

# app.py
@app.route('/student/<int:student_id>/fee_records')
@login_required
def view_fee_records(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('view_fee_records.html', student=student)

@app.route('/all_fee_records')
@login_required
def view_all_fee_records():
    fee_records = FeeRecord.query.join(Student).all()
    return render_template('view_all_fee_records.html', fee_records=fee_records)


if __name__ == '__main__':
    app.run(debug=True,port=5051)
