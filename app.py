# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import ipinfo
from user_agents import parse
from datetime import datetime
# from camera import capture_and_upload_frames
from inference import infer, loginInfer
from face_to_encoding import encodeSet, encodeByPerson, checkValidCamInput
from train import train
from models import db, User, Connection, LogEvent
import random
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.fastmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'team1test@fastmail.com'
app.config['MAIL_PASSWORD'] = '85jj5xcqfy3ypk3q'

# Secret key for sessions
app.secret_key = 'test'

# Assuming we have a single user for demonstration purposes
# In a real-world scenario, you would use a database
user_info = {
    "admin" : generate_password_hash("password123"),  #temp, should not Never store passwords in plain text
    "Justin_Sun": generate_password_hash("password123"),
}

mail = Mail(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'image')
ENCODINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'encodings.txt')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ENCODINGS_PATH'] = ENCODINGS_PATH
app.config['SERVER_PORT'] = int(os.getenv('SERVER_PORT', 5000)) # Default to 5000 if not set
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

app.app_context().push()
db.init_app(app)
# Create tables if they do not exist already
db.drop_all()
db.create_all()

for user in user_info.keys():
    test_user = User(
        email=user,
        password=user_info.get(user),
    )
    db.session.add(test_user)
    db.session.commit()

print(db.session.execute(db.select(User).filter_by(email="admin")).scalar_one().connections)


# Generate model using encodings
if not os.path.exists(app.config['ENCODINGS_PATH']):
    encodeSet(UPLOAD_FOLDER, app.config['ENCODINGS_PATH'])
    train(app.config['ENCODINGS_PATH'])
else:
    train(app.config['ENCODINGS_PATH'])

def generate_verification_code():
    return str(random.randint(100000, 999999))

@app.route('/')
def index():
    if 'username' in session and session.get('authenticated', True):
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'username' not in session or not session.get('authenticated', False):
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if db.session.query(User.email).filter_by(email=username).scalar() is not None:
            hashed_pw = db.session.execute(db.select(User).filter_by(email=username)).scalar_one().password
            if check_password_hash(hashed_pw, password):
                session['username'] = username
                return redirect(url_for('faceID'))
            else:
                flash('Invalid username or password!')
        else:
            flash('Invalid username or password!')

    return render_template('index.html')

@app.route('/faceID', methods=['GET','POST'])
def faceID():
    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('login'))
        username = session['username']

        frames = []
        testFileName = "" # Temporary solution, should be changed
        for i in range(len(request.files)):
            frame = request.files['frame_' + str(i)]
            filename = secure_filename(frame.filename)
            
            # Generate a unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as file:
                file.write(frame.read())
            frames.append(frame)

            testFileName = filepath # Temporary solution, should be changed
       
        # For demonstration assumin authentication is successful
        result = infer(testFileName)
        if (result != None and result[0] == username):
            print('Face recognized for '+ username)
            session['authenticated'] = True
            return jsonify({'redirect': url_for('home')})  # Return JSON response with redirect URL
        else:
            print('Face not recognized')
            return jsonify({'message': 'Face not recognized. Please Try Again'})  # Return JSON response with message
    else:
        return render_template('faceID.html', username=session['username'])

@app.route('/logout')
def logout():
    session['authenticated'] = False
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_agent = parse(request.user_agent.string)
        verification_code = generate_verification_code()
        global email_waitfor_verify 
        email_waitfor_verify = email
        ip = request.remote_addr
        # Store the registration data in the user_info dictionary
        user_info[email] = {
            'password': generate_password_hash(password),
            'verification_code': verification_code
        }

        frames = []
        index = 0
        while f'faceImages_{index}' in request.files:
            frame = request.files[f'faceImages_{index}']
            
            # Generate a unique filename with timestamp and index
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{email}_{timestamp}_{index}.{frame.filename.split('.')[-1]}"
            
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], email), exist_ok=True)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], email, filename)
            frame.save(save_path)
            frames.append(frame)
            index += 1

        if email and password and frames:
            if checkValidCamInput(app.config['UPLOAD_FOLDER'] + '/' + email, 30):
                # check if the face registration in register.html is successful
                success = True

                # Initailize models
                encodeByPerson(app.config['UPLOAD_FOLDER'], email, app.config['ENCODINGS_PATH'])
                train(app.config['ENCODINGS_PATH'])

                if success:
                    email_string = "Thank you for registering! Please enter the following code to activate your account: " + str(verification_code)
                    msg = Message('Registration Confirmation', sender='team1test@fastmail.com', recipients=[email])
                    msg.body = email_string
                    mail.send(msg)
                    print("User info after registration:")
                    print(user_info)
                    print(email)
                    new_user = User(
                        email=email,
                        password=generate_password_hash(password),
                    )
                    new_user_connection = Connection(
                        device=str(user_agent).split(' / ')[0],
                    )
                    new_user.connections.append(new_user_connection)
                    db.session.add(new_user)
                    db.session.add(new_user_connection)
                    db.session.commit()
                    return redirect(url_for('verification', email=email))
                else:
                    message = 'Registration failed.'
            else:
                message = 'Registration failed.'
        else:
            message = 'Registration failed.'
        
        return jsonify({'message': message})
    return render_template('register.html')

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/process_scans', methods=['POST'])
def process_scans():
    scans = request.json
    # Process the scan data
    for step, image_data in scans.items():
        # TODO: Process each image_data, for example, save to a file or a database
        print(f"Received scan for {step}")

    
    #  might want to implement actual success checking logic based on processing
    return jsonify({'success': True})

@app.route('/verification', methods=['GET', 'POST'])
def verification():
    if request.method == 'POST':
        data = request.get_json()
        email = email_waitfor_verify
        #email = data.get('email')
        verification_code = data.get('verification_code')

        print(data)
        print("User info after registration:")
        print(user_info)
        print("The email-------------------------------------")
        print(email)
        print("The email-------------------------------------")
        print("The verification_code-------------------------------------")
        print(verification_code)
        print("The verification_code-------------------------------------")

        if email in user_info:
            if user_info[email]['verification_code'] == verification_code:
                # Verification code is correct
                # Mark the email as verified in the user_info dictionary or your database
                user_info[email]['verified'] = True
                
                return {'success': True}
            else:
                # Verification code is incorrect
                return {'success': False, 'message': 'Invalid verification code. Please try again.'}
        else:
            # Invalid email
            return {'success': False, 'message': 'Email is missing'}
    else:
        email = request.args.get('email')
        return render_template('verification.html', email=email)

# ... other route definitions ...

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=app.config['SERVER_PORT'], ssl_context='adhoc')

