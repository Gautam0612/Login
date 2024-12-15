from flask import Flask, jsonify, request,session,url_for,redirect
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import string
import os
from datetime import timedelta , datetime
from dotenv import load_dotenv
import jwt


# Configuration
load_dotenv()
app = Flask(__name__)
bcrypt = Bcrypt(app)
secret_key = os.urandom(24)
mongo_url = os.getenv('MONGO_URL')

app.config['PERMANENT_SESSION_LIFETIME']= timedelta(minutes=2)
app.secret_key = secret_key
client = MongoClient(
    mongo_url)
db = client['userData']
collection = db['Data']

def generate_otp(length=6):
    digits = string.digits
    otp = ''.join(random.choice(digits) for i in range(length))
    return otp
    

@app.route("/testing",methods=['GET'])
def testing():
    try:
         return jsonify({ 'message': "Running"})
        
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# @app.route()   \
def send_email_otp(sender_email, sender_password, recipient_email, otp_subject, otp_body):
    try:
        # Set up the MIME
        message = MIMEMultipart()
        print(sender_email)
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = otp_subject

        # Add body to the email
        message.attach(MIMEText(otp_body, 'plain'))

        # Create SMTP session for sending the mail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable security
        server.login(sender_email, sender_password)  # Login with sender's email and password
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_otp():
    # Extract data from the POST request
    data = request.json
    # recipient_email = data.get('recipient_email')
    recipient_email="gautam.gs125@gmail.com"
    otp_subject = data.get('otp_subject', 'Your OTP Code')

    # Generate OTP and store in session
    otp = generate_otp()
    session['otp'] = otp
    otp_body = f'Your OTP is {otp}'

    # Sender email credentials (in a real application, do not hardcode these credentials)
    sender_email = os.getenv('sender_email')
    sender_password = os.getenv('sender_password')

    # Call the send_email_otp function
    if send_email_otp(sender_email, sender_password, recipient_email, otp_subject, otp_body):
        return jsonify({'message': 'OTP sent successfully'}), 200
    else:
        return jsonify({'message': 'Failed to send OTP'}), 500
def send_alert(email):
    try:
        send_email_otp("gautam.gs712@gmail.com" , "bigv rqeo incb dcht", email , "Alert", "Your account has been logged in from a new device")
    except Exception as e:
        return jsonify({'message':e})
@app.route("/signup", methods=['POST'])
def sign():
    try:
        data = request.json
        name = data['name']
        username = data['username']
        password = data['password']
        email = data['email']
        
        # Check if the user already exists
        existing = collection.find_one({'email': email})
        existingusername = collection.find_one({'username': username})
        if existing:
            return jsonify({'message': "Already registered"})
        elif existingusername:
            return jsonify({'message': "Username not available"})
        
        # Generate OTP and send email
        otp = generate_otp()
        sender_email = os.getenv('sender_email')
        sender_password = os.getenv('sender_password')
        if not send_email_otp(sender_email, sender_password, email, 'Your OTP Code', f'Your OTP is {otp}'):
            return jsonify({'message': 'Failed to send OTP'}), 500
        
        # Store user data and OTP in session for later verification
        session['user_data'] = {
            'name': name,
            'username': username,
            'password': bcrypt.generate_password_hash(password).decode('utf-8'),
            'email': email
        }
        session['otp'] = otp
        session['otp_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({'message': 'OTP sent successfully', 'email': email})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route("/verify_otp", methods=['POST'])
def verify_otp():
    try:
        data = request.json
        input_otp = data['otp']
        
        user_data = session.get('user_data')
        session_otp = session.get('otp')
        otp_timestamp_str = session.get('otp_timestamp')
        
        if user_data and session_otp and otp_timestamp_str:
            otp_timestamp = datetime.strptime(otp_timestamp_str, '%Y-%m-%d %H:%M:%S')
            if datetime.now() - otp_timestamp > timedelta(minutes=5):
                return jsonify({'message': 'OTP has expired'}), 400
            
            if input_otp == session_otp:
                collection.insert_one(user_data)
                session.pop('user_data', None)
                session.pop('otp', None)
                session.pop('otp_timestamp', None)
                send_alert(user_data['email'])
                return jsonify({'message': 'User verified and created successfully'})
            else:
                return jsonify({'message': 'Invalid OTP'}), 400
        else:
            return jsonify({'message': 'Session expired or invalid'}), 400

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# route to check if the user is logged in or not
@app.route("/", methods=['POST'])
def check():
    try:
        if 'email' in session:
            return jsonify({'message': 'User is logged in'})
        else:
            return redirect(url_for('signin'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def sendResponse(email):
    try:
        token = jwt.encode({'email': email}, secret_key, algorithm='HS256')
        return jsonify({'email':email,'Token': token,'type':'1'})
    except Exception as e:
        return jsonify({'message':e})

@app.route("/signin", methods=['POST','GET'])
def signin():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        if email in session:
            print('2')
            return sendResponse(email)
        user = collection.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            # token = jwt.encode({'email': email}, secret_key, algorithm='HS256')
            token = jwt.encode({'email': email}, secret_key, algorithm='HS256')
            # otp = generate_otp()
            session['email'] = email
            return jsonify({'email': email,'token': token , 'type':'2'})
        else:
            return jsonify({'message': 'User not found or incorrect password'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        newpass = data['newpassword']

        user = collection.find_one({'email': email})

        if user and user['password'] == password:
            collection.update_one(
                {'email': email}, {'$set': {'password': newpass}})
            return jsonify({"message": "Password updated successfully"})
        else:
            return jsonify({"message": "User not found or incorrect password"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete', methods=['DELETE'])
def delete():
    try:
        data = request.json
        email = data['email']
        password = data['password']

        user = collection.find_one({'email': email})

        if user and user['password'] == password:
            collection.delete_one({'email': email})
            return jsonify({"message": "User deleted successfully"})
        else:
            return jsonify({"message": "User not found or incorrect password"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080,debug=True)
