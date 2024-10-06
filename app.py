from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Dummy data for students and rooms
students = {}
rooms = {}

# Homepage Route
@app.route('/')
def home():
    return render_template('home.html')

# Student Login
@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

# Admin Login
@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')

# Room Management (Admin Only)
@app.route('/room_management')
def room_management():
    return render_template('room_management.html')

# Student Registration
@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
