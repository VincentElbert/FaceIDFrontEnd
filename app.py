# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from camera import capture_and_upload_frames

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Assuming we have a single user for demonstration purposes
# In a real-world scenario, you would use a database
user_info = {
    "username": "admin",
    "password": generate_password_hash("password123")  # Never store passwords in plain text
}

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == user_info['username'] and check_password_hash(user_info['password'], password):
            session['username'] = user_info['username']
            return redirect(url_for('faceID'))
        else:
            flash('Invalid username or password!')

    return render_template('index.html')

@app.route('/faceID', methods=['GET','POST'])
def faceID():
    capture_and_upload_frames()
    return redirect(url_for("home"))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)