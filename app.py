# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import base64
# from camera import capture_and_upload_frames

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Assuming we have a single user for demonstration purposes
# In a real-world scenario, you would use a database
user_info = {
    "admin" : generate_password_hash("password123")  # Never store passwords in plain text
}

UPLOAD_FOLDER = 'C:\\Users\\USER\\Desktop\\FDM\\FaceIDFrontEnd\\resources\\image'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

        if check_password_hash(user_info[username], password):
            session['username'] = username
            return redirect(url_for('faceID'))
        else:
            flash('Invalid username or password!')

    return render_template('index.html')

@app.route('/faceID', methods=['GET','POST'])
def faceID():
    if request.method == 'POST':
        frames = []
        for i in range(len(request.files)):
            frame = request.files['frame' + str(i)]
            filename = secure_filename(frame.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as file:
                file.write(frame.read())
            frames.append(frame)
        # Process the received frames for face scanning
        # Implement your face scanning logic here
        # For demonstration purposes, let's assume authentication is successful
        if frames:
            return redirect(url_for('home'))
        else:
            flash('Face not recognized')
    else:
        return render_template('faceid.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        email = data['email']
        password = data['password']
        face_images = data['faceImages']

        # Store the registration data in the user_info dictionary
        user_info[email] = generate_password_hash(password)
        if email and password and face_images:
            # check if the face registration in register.html is successful
            success = True
            if success:
                message = 'Registration successful!'
            else:
                message = 'Registration failed.'

        return jsonify(message)
    return render_template('register.html')

@app.route('/process_scans', methods=['POST'])
def process_scans():
    scans = request.json
    # Process the scan data
    for step, image_data in scans.items():
        # TODO: Process each image_data, for example, save to a file or a database
        print(f"Received scan for {step}")

    # After processing the scans, return a success response
    # You might want to implement actual success checking logic based on your processing
    return jsonify({'success': True})

# ... other route definitions ...

if __name__ == '__main__':
    app.run(debug=True)

