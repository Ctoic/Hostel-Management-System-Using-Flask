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
from calendar import month_name
from sqlalchemy import extract
import pandas as pd
import openpyxl


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
    # Get current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Get total number of active students
    total_students = Student.query.filter_by(status='active').count()

    # Get monthly expenses for the last 6 months
    monthly_expenses = []
    monthly_income = []
    months = []
    
    for i in range(5, -1, -1):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
            
        # Get expenses for the month
        month_expenses = Expense.query.filter(
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == month
        ).all()
        total_expense = sum(expense.price for expense in month_expenses)
        
        # Get income (fee collections) for the month
        month_income = FeeRecord.query.filter(
            db.extract('year', FeeRecord.date_paid) == year,
            db.extract('month', FeeRecord.date_paid) == month
        ).all()
        total_income = sum(record.amount for record in month_income)
        
        monthly_expenses.append(total_expense)
        monthly_income.append(total_income)
        months.append(month_name[month][:3])  # Short month name

    # Get expense categories for pie chart
    expense_categories = db.session.query(
        Expense.item_name,
        db.func.sum(Expense.price).label('total')
    ).group_by(Expense.item_name).all()
    
    # Calculate total expenses and income for the current month
    current_month_expenses = sum(monthly_expenses[-1:])
    current_month_income = sum(monthly_income[-1:])
    
    # Calculate profit/loss
    profit_loss = current_month_income - current_month_expenses
    
    # Get fee collection status
    fully_paid = Student.query.filter_by(status='active').filter(
        Student.fee_status == 'paid'
    ).count()
    partially_paid = Student.query.filter_by(status='active').filter(
        Student.fee_status == 'partial'
    ).count()
    unpaid = Student.query.filter_by(status='active').filter(
        Student.fee_status == 'unpaid'
    ).count()

    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         monthly_expenses=monthly_expenses,
                         monthly_income=monthly_income,
                         months=months,
                         expense_categories=expense_categories,
                         current_month_expenses=current_month_expenses,
                         current_month_income=current_month_income,
                         profit_loss=profit_loss,
                         fully_paid=fully_paid,
                         partially_paid=partially_paid,
                         unpaid=unpaid)

# Room Management (Admin Only)
@app.route('/room_management')
@login_required
def room_management():
    return render_template('room_management.html')

# Add this function at the beginning of app.py
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls'}
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

@app.template_filter('month_name')
def month_name_filter(month_number):
    return month_name[month_number]


# from calendar import month_name

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    form = ExpenseForm()
    
    # Get filter parameters (default to current month and year)
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)

    # Get the previous month's data
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    # Query expenses for the current month and year
    expenses_current = Expense.query.filter(
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).order_by(Expense.date.desc()).all()

    # Query expenses for the previous month and year
    expenses_previous = Expense.query.filter(
        extract('year', Expense.date) == prev_year,
        extract('month', Expense.date) == prev_month
    ).order_by(Expense.date.desc()).all()

    # Calculate totals for both months
    total_expenses_current = sum(expense.price for expense in expenses_current)
    total_expenses_previous = sum(expense.price for expense in expenses_previous)

    # Get fee collections for current month
    fee_records_current = FeeRecord.query.filter(
        extract('year', FeeRecord.date_paid) == year,
        extract('month', FeeRecord.date_paid) == month
    ).all()
    total_income_current = sum(record.amount for record in fee_records_current)

    # Get fee collections for previous month
    fee_records_previous = FeeRecord.query.filter(
        extract('year', FeeRecord.date_paid) == prev_year,
        extract('month', FeeRecord.date_paid) == prev_month
    ).all()
    total_income_previous = sum(record.amount for record in fee_records_previous)

    # Calculate remaining balance
    remaining_balance_current = total_income_current - total_expenses_current
    remaining_balance_previous = total_income_previous - total_expenses_previous

    if form.validate_on_submit():
        expense = Expense(
            item_name=form.item_name.data,
            price=form.price.data,
            date=form.date.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))

    return render_template('expenses.html', 
                         form=form,
                         expenses_current=expenses_current,
                         expenses_previous=expenses_previous,
                         total_expenses_current=total_expenses_current,
                         total_expenses_previous=total_expenses_previous,
                         total_income_current=total_income_current,
                         total_income_previous=total_income_previous,
                         remaining_balance_current=remaining_balance_current,
                         remaining_balance_previous=remaining_balance_previous,
                         current_month=month,
                         current_year=year,
                         prev_month=prev_month,
                         prev_year=prev_year,
                         month_names=month_name)

@app.route('/export_pdf/<int:year>/<int:month>', methods=['GET'])
def export_pdf(year, month):
    # Get expenses for the specified month and year
    expenses = Expense.query.filter(
        db.extract('year', Expense.date) == year,
        db.extract('month', Expense.date) == month
    ).all()

    # Calculate total expenses for the month
    total_expenses = sum(expense.price for expense in expenses)
    
    # Get total income from fee records for the month
    total_income = db.session.query(db.func.sum(FeeRecord.amount)).filter(
        db.extract('year', FeeRecord.date_paid) == year,
        db.extract('month', FeeRecord.date_paid) == month
    ).scalar() or 0

    # Calculate remaining balance
    remaining_balance = total_income - total_expenses

    # Create a BytesIO buffer for the PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title section
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, height - 50, f"Monthly Expense Report - {month}/{year}")

    # Income and Expense Summary
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 100, f"Total Income: Rs {total_income}")
    pdf.drawString(50, height - 120, f"Total Expenses: Rs {total_expenses}")
    pdf.drawString(50, height - 140, f"Remaining Balance: Rs {remaining_balance}")

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

# Admin Registration

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



@app.route('/collect_fee', methods=['GET', 'POST'])
@login_required
def collect_fee():
    form = FeeCollectionForm()

    # Get the month and year filter parameters
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)

    # Get all active students
    active_students = Student.query.filter_by(status='active').all()

    # Categorize students based on their payment status
    fully_paid_students = []
    partially_paid_students = []
    unpaid_students = []
    
    for student in active_students:
        if student.fee_status == 'paid':
            fully_paid_students.append(student)
        elif student.fee_status == 'partial':
            partially_paid_students.append(student)
        else:
            unpaid_students.append(student)

    # Get fee records for the selected month and year
    fee_records = FeeRecord.query.filter(
        db.extract('year', FeeRecord.date_paid) == year,
        db.extract('month', FeeRecord.date_paid) == month
    ).join(Student).all()

    # Calculate total fee collected for the month
    total_fee = sum(record.amount for record in fee_records)

    if form.validate_on_submit():
        student_name = form.student_name.data
        amount = form.amount.data
        date_paid = form.date.data
        
        student = Student.query.filter_by(name=student_name).first()

        if student:
            # Check if the payment would exceed the total fee
            if amount > student.remaining_fee:
                flash(f'Payment amount exceeds remaining fee of Rs {student.remaining_fee}!', 'warning')
            else:
                fee_record = FeeRecord(
                    student_id=student.id,
                    amount=amount,
                    date_paid=date_paid
                )
                student.last_fee_payment = date_paid
                db.session.add(fee_record)
                db.session.commit()
                flash('Fee payment recorded successfully!', 'success')
                return redirect(url_for('collect_fee'))
        else:
            flash('Student not found', 'danger')

    return render_template('collect_fee.html', 
                         form=form, 
                         fee_records=fee_records, 
                         total_fee=total_fee, 
                         current_month=month, 
                         current_year=year, 
                         month_name=month_name,
                         fully_paid_students=fully_paid_students,
                         partially_paid_students=partially_paid_students,
                         unpaid_students=unpaid_students)


@app.template_filter('month_name')  # Register the filter       
def month_name_filter(month_number):
    return month_name[month_number]

@app.route('/update_students_excel', methods=['GET', 'POST'])
@login_required
def update_students_excel():
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['excel_file']
        if file and allowed_file(file.filename):
            try:
                # Read the Excel file
                print(f"Reading Excel file: {file.filename}")  # Debug log
                df = pd.read_excel(file)
                print(f"Excel data shape: {df.shape}")  # Debug log
                print(f"Excel columns: {df.columns.tolist()}")  # Debug log
                
                # Process each row
                for index, row in df.iterrows():
                    print(f"Processing row {index}: {row.to_dict()}")  # Debug log
                    student = Student.query.filter_by(name=row['name']).first()
                    
                    if student:
                        print(f"Updating existing student: {student.name}")  # Debug log
                        # Update existing student
                        student.fee = float(row['fee'])
                        student.room_id = int(row['room_id'])
                        student.status = row.get('status', 'active')
                        
                        # Update picture if provided
                        if 'picture' in row and pd.notna(row['picture']):
                            picture_filename = secure_filename(row['picture'])
                            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], picture_filename)):
                                student.picture = picture_filename
                    else:
                        print(f"Creating new student: {row['name']}")  # Debug log
                        # Create new student
                        new_student = Student(
                            name=row['name'],
                            fee=float(row['fee']),
                            room_id=int(row['room_id']),
                            status=row.get('status', 'active')
                        )
                        
                        # Set picture if provided
                        if 'picture' in row and pd.notna(row['picture']):
                            picture_filename = secure_filename(row['picture'])
                            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], picture_filename)):
                                new_student.picture = picture_filename
                            else:
                                print(f"Warning: Picture file not found for student: {row['name']}")
                        
                        db.session.add(new_student)
                
                print("Committing changes to database...")  # Debug log
                db.session.commit()
                print("Changes committed successfully")  # Debug log
                flash('Student data updated successfully!', 'success')
                return redirect(url_for('students'))
                
            except Exception as e:
                print(f"Error processing Excel file: {str(e)}")  # Debug log
                db.session.rollback()
                flash(f'Error processing Excel file: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Invalid file format. Please upload an Excel file (.xlsx or .xls)', 'danger')
            return redirect(request.url)
            
    return render_template('update_students_excel.html')

@app.route('/download_sample_excel')
@login_required
def download_sample_excel():
    # Create a sample DataFrame
    df = pd.DataFrame({
        'name': ['John Doe', 'Jane Smith'],
        'fee': [5000, 6000],
        'room_id': [1, 2],
        'status': ['active', 'active'],
        'picture': ['student1.jpg', 'student2.jpg']  # Add picture field
    })
    
    # Create a BytesIO buffer
    buffer = BytesIO()
    
    # Write the DataFrame to Excel
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Students')
    
    # Set the buffer position to the beginning
    buffer.seek(0)
    
    # Send the file
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_student_template.xlsx'
    )

if __name__ == '__main__':  
    with app.app_context():
        create_tables()
    app.run(debug=True,port=5051)
