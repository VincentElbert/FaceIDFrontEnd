# app.py
from datetime import datetime, timedelta

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
from concurrent.futures import ThreadPoolExecutor
import random
from sqlalchemy import text 
from sqlalchemy.orm.exc import NoResultFound
from flask_mail import Mail, Message
import json

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.fastmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'facedefensemaster@fastmail.com'
app.config['MAIL_PASSWORD'] = '75q5cyy7nemdus8h'
#app.config['MAIL_USERNAME'] = 'team1test@fastmail.com'
# app.config['MAIL_PASSWORD'] = '85jj5xcqfy3ypk3q'

# Secret key for sessions
app.secret_key = 'test'

# Assuming we have a single user for demonstration purposes
# In a real-world scenario, you would use a database
user_info = {
    "admin" : generate_password_hash("password123"),  #temp, should not Never store passwords in plain text
    "Justin_Sun": generate_password_hash("password123"),
}


mail = Mail(app)
ipinfo_token = "3fcc779048091b"
ip_handler = ipinfo.getHandler(ipinfo_token)

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
    if 'username' not in session or not session.get('authenticated', False) or not db.session.query(User.email).filter_by(email=session['username']).scalar():
        return redirect(url_for('login'))
    username=session['username']
    user = db.session.execute(db.select(User).filter_by(email=username)).scalar_one()
    connections = [serialize_connection(connection) for connection in user.connections]
    histories = [serialize_history(event) for event in user.logevent]
    return render_template('home.html', username=username, connections=json.dumps(connections), histories=json.dumps(histories))

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('username', None)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if db.session.query(User.email).filter_by(email=username).scalar():
            hashed_pw = db.session.execute(db.select(User).filter_by(email=username)).scalar_one().password
            if check_password_hash(hashed_pw, password):
                session['username'] = username
                return redirect(url_for('faceID'))
            else:
                user = db.session.execute(db.select(User).filter_by(email=username)).scalar_one()
                new_failed_login = LogEvent(
                    user_email=username,
                    time=datetime.now(),
                    event_desc="Login Failed - Incorrect Password",
                    ip=request.remote_addr,
                    location=ip_handler.getDetails(request.remote_addr).country_name
                        if hasattr(ip_handler.getDetails(request.remote_addr), "country_name")
                        else "Location Undetectable",
                    device=": ".join(str(user_agent).split(' / ')[:1]),
                )
                user.logevent.append(new_failed_login)
                db.session.add(new_failed_login)
                db.session.commit()
                flash('Invalid username or password!')
        else:
            flash('Invalid username or password!')

    return render_template('index.html')

@app.route('/faceID', methods=['GET','POST'])
def faceID():
    if 'username' not in session:
        return redirect(url_for('login'))
    session['authenticated'] = False
    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('login'))
        username = session['username']
        user = db.session.execute(db.select(User).filter_by(email=username)).scalar_one()

        frames = []
        # testFileName = "" # Temporary solution, should be changed
        for i in range(len(request.files)):
            frame = request.files['frame_' + str(i)]
            # filename = secure_filename(frame.filename)
            
            ## Generate a unique filename with timestamp
            # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # filename = f"{timestamp}_{filename}"
            
            # filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # with open(filepath, 'wb') as file:
            #    file.write(frame.read())
            frames.append(frame)

            # testFileName = filepath # Temporary solution, should be changed
    
        # For demonstration assumin authentication is successful
        # result = infer(testFileName)
        result = infer(frames[0].stream)
        if (result != None and result[0] == username):
            print('Face recognized for '+ username)
            session['authenticated'] = True
            new_login = LogEvent(
                user_email=username,
                time=datetime.now(),
                event_desc="Login Success",
                ip=request.remote_addr,
                location=ip_handler.getDetails(request.remote_addr).country_name
                if hasattr(ip_handler.getDetails(request.remote_addr), "country_name")
                else "Location Undetectable",
                device=": ".join(str(user_agent).split(' / ')[:1]),
            )
            user.logevent.append(new_login)
            db.session.add(new_login)
            db.session.commit()
            return jsonify({'redirect': url_for('home')})  # Return JSON response with redirect URL
        else:
            new_failed_login = LogEvent(
                user_email=username,
                time=datetime.now(),
                event_desc="Login Failed - Failed Face Recognition",
                ip=request.remote_addr,
                location=ip_handler.getDetails(request.remote_addr).country_name
                if hasattr(ip_handler.getDetails(request.remote_addr), "country_name")
                else "Location Undetectable",
                device=": ".join(str(user_agent).split(' / ')[:1]),
            )
            user.logevent.append(new_failed_login)
            db.session.add(new_failed_login)
            db.session.commit()
            print('Face not recognized')
            return jsonify({'message': 'Face not recognized. Please Try Again'})  # Return JSON response with message
    else:
        return render_template('faceID.html', username=session['username'])

@app.route('/recoveryFaceID', methods=['GET','POST'])
def recoveryFaceID():
    verification_code = generate_verification_code()
    # user_info[email] = {
    # 'password': generate_password_hash(password),
    # 'verification_code': verification_code,
    # }
    if request.method == 'POST': 
        frames = []
        for i in range(len(request.files)):
            frame = request.files['frame_' + str(i)]

            frames.append(frame)
        result = infer(frames[0].stream)
        if (result != None and str(result[0]) != "N" and result[0]):
            email = str(result[0])
            print('Result is: --------------------- ' + str(result))
            print('Face recognized for '+ str(result[0]))
            user_info[email]['verification_code'] = verification_code
            user_info[email]['Recoverying'] = True
            print(verification_code)
            send_email(email,verification_code)
            response = {
                'redirect': url_for('verification'),
                'email': email,
                'recovery': True
            }
            return jsonify(response)
            # return redirect(url_for('verification', email=result[0], recovery=True))  # Return JSON response with redirect URL
        else:
            print('Face not recognized')
            return jsonify({'message': 'Face not recognized. Please Try Again'})  # Return JSON response with message
    else:
        return render_template('recoveryFaceID.html')

@app.route('/logout')
def logout():
    session['authenticated'] = False
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        global password
        password = request.form.get('password')
        global user_agent
        user_agent = parse(request.user_agent.string)
        verification_code = generate_verification_code()
        global email_waitfor_verify 
        email_waitfor_verify = email
        ip = request.remote_addr
        # Store the registration data in the user_info dictionary
        user_info[email] = {
            'password': generate_password_hash(password),
            'verification_code': verification_code,
        }
        
        if email and password and request.files:
            try:
                encodings = []
                for index in range(len(request.files)):
                    if f'faceImages_{index}' in request.files:
                        person_img = request.files[f'faceImages_{index}']
                        encodingLine = encodeByPerson(person_img)
                        if encodingLine:
                            encodings.append(encodingLine)

                if encodings:
                    with open(app.config['ENCODINGS_PATH'], "a") as file:
                        file.write("\n")
                        file.write("\n".join([email + encoding for encoding in encodings]))
                    train(app.config['ENCODINGS_PATH'])
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    user_info[email]['timestamp'] = timestamp  # Add the timestamp to the existing user_info[email] dictionary
                    send_email(email_waitfor_verify,verification_code)
                    print("User info after registration:")
                    print(user_info)
                    print(email)

                    return jsonify({'message': 'Registration successful!'})
                else:
                    return jsonify({'message': 'Registration failed.'})
            except Exception as e:
                print(f"Error during registration: {str(e)}")
                return jsonify({'message': 'Registration failed.'})
        else:
            return jsonify({'message': 'Registration failed.'})
    return render_template('register.html')


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('password')

        user = db.session.query(User).filter(User.email == email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            return jsonify({'message': 'Reset password successful!'})

        else:
            print("User not found.")
    else:
        email = request.args.get('email')
        return render_template('reset.html', email= email)

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
        recovery = data.get('recovery')
        print("The email wait for verify:-----------------------------------  " + email)

        if email in user_info:
            if user_info[email]['verification_code'] == verification_code and recovery != 'true':
                current_timestamp = datetime.now()
                
                # Get the registration timestamp from user_info
                registration_timestamp_str = user_info[email]['timestamp']
                registration_timestamp = datetime.strptime(registration_timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # Calculate the timestamp 5 minutes ago
                five_minutes_ago = current_timestamp - timedelta(seconds=60)

                if registration_timestamp > five_minutes_ago:
                        
                        # Verification code is correct
                        # Mark the email as verified in the user_info dictionary or your database
                        user_info[email]['verified'] = True
                        new_user = User(
                            email=email,
                            password=generate_password_hash(password),
                        )
                        new_user_connection = Connection(
                            device=": ".join(str(user_agent).split(' / ')[:1]),
                        )
                        new_creation = LogEvent(
                            user_email=email,
                            time=datetime.now(),
                            event_desc="Create Account",
                            ip=request.remote_addr,
                            location=ip_handler.getDetails(request.remote_addr).country_name
                            if hasattr(ip_handler.getDetails(request.remote_addr), "country_name")
                            else "Location Undetectable",
                            device=": ".join(str(user_agent).split(' / ')[:1]),
                        )

                        try:
                            if user_info[email]['Recoverying']:
                                del user_info[email]['Recoverying']
                        except KeyError:
                            pass
                            
                        new_user.connections.append(new_user_connection)
                        new_user.logevent.append(new_creation)
                        db.session.add(new_user)
                        db.session.add(new_user_connection)
                        db.session.add(new_creation)
                        db.session.commit()

                        return {'success': 'true', 'recovery': 'false'}
                    
                else:

                    return {'success': False, 'message': 'Verification code has expired. Please request a new one.'}

            elif user_info[email]['verification_code'] == verification_code and recovery == 'true':
                return {'success': 'true', 'recovery': 'true'}
            else:
                return {'success': 'false', 'message': 'Invalid verification code. Please try again.'}
        else:
            # Invalid email
            return {'success': 'false', 'message': 'Email is missing'}
    else:
        email = request.args.get('email')
        recovery = request.args.get('recovery')
        return render_template('verification.html', email=email, recovery=recovery)
    
def send_email(email_waitfor_verify, verification_code):
    try:
        if user_info[email_waitfor_verify]['Recoverying']:
            print('code for Recoveryinging sending')
            email_string = """
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        padding: 20px;
                        margin: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        padding: 0;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                        border: 1px solid #000000;
                    }}
                    h1 {{
                        color: #ffffff;
                        background-color: #ff6600;
                        padding: 20px;
                        margin: 0;
                        text-align: center;
                        border-top-left-radius: 1px;
                        border-top-right-radius: 1px;
                    }}
                    p {{
                        color: #666666;
                        line-height: 1.5;
                        padding: 20px;
                        margin: 0;
                    }}
                    .code {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #ff6600;
                        text-align: center;
                        margin: 20px 0;
                        padding: 10px;
                        background-color: #f9f9f9;
                        border: 2px solid #e0e0e0;
                        border-radius: 5px;
                    }}
                    .expiration {{
                        color: #999999;
                        text-align: center;
                        margin: 0;
                        padding-bottom: 20px;
                    }}
                    .simpletext {{
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Account Recovery</h1>
                    <p class="simpletext">Please enter the following code to proceed to your account recovery:</p>
                    <div class="code">{verification_code}</div>
                    <p class="expiration">The code will expire in 5 minutes.</p>
                    <p class="simpletext">If you have any questions or need assistance, feel free to contact our support team via itsupport@FaceDefenseMaster.com</p>
                </div>
            </body>
            </html>
            """
            msg = Message('Reset Password', sender='facedefensemaster@fastmail.com', recipients=[email_waitfor_verify])
            msg.html = email_string.format(verification_code=verification_code)
            mail.send(msg)
            print("Code for account recovery sent")
    except KeyError:
        email_string = """
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                    margin: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 0;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                    border: 1px solid #000000;
                }}
                h1 {{
                    color: #ffffff;
                    background-color: #ff6600;
                    padding: 20px;
                    margin: 0;
                    text-align: center;
                    border-top-left-radius: 1px;
                    border-top-right-radius: 1px;
                }}
                p {{
                    color: #666666;
                    line-height: 1.5;
                    padding: 20px;
                    margin: 0;
                }}
                .code {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #ff6600;
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f9f9f9;
                    border: 2px solid #e0e0e0;
                    border-radius: 5px;
                }}
                .expiration {{
                    color: #999999;
                    text-align: center;
                    margin: 0;
                    padding-bottom: 20px;
                }}
                .simpletext {{
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to Face Denfense Master!</h1>
                <p class="simpletext">Please enter the following code to proceed to activate your account:</p>
                <div class="code">{verification_code}</div>
                <p class="expiration">The code will expire in 5 minutes.</p>
                <p class="simpletext">If you have any questions or need assistance, feel free to contact our support team via itsupport@FaceDefenseMaster.com</p>
            </div>
        </body>
        </html>
        """
        msg = Message('Registration Confirmation', sender='facedefensemaster@fastmail.com', recipients=[email_waitfor_verify])
        msg.html = email_string.format(verification_code=verification_code)
        mail.send(msg)
        print("Code for account registration sent")


@app.route('/resend_verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        verification_code = generate_verification_code()
        user_info[email_waitfor_verify]['verification_code'] = verification_code
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_info[email_waitfor_verify]['timestamp'] = timestamp  # Add the timestamp to the existing user_info[email] dictionary
        print(user_info)
        send_email(email_waitfor_verify,verification_code)
        return render_template('verification.html')
    else:
        return render_template('verification.html')
    
def serialize_connection(connection):
    return {
        'cid': str(connection.cid),
        'device': connection.device
    }

def serialize_history(event):
    return {
        'eid': str(event.eid),
        'device': event.device,
        'time': str(event.time),
        'ip': event.ip,
        'location': event.location,
        'event_desc': event.event_desc
    }


# ... other route definitions ...

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=app.config['SERVER_PORT'], ssl_context='adhoc')

