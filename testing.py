from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
app.secret_key = 'supersecretkey'  # Change this to a more secure key

# Function to generate a random OTP
def generate_otp(length=6):
    digits = string.digits
    otp = ''.join(random.choice(digits) for i in range(length))
    return otp

# Function to send OTP via email
def send_email_otp(sender_email, sender_password, recipient_email, otp_subject, otp_body):
    try:
        # Set up the MIME
        message = MIMEMultipart()
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

@app.route('/send-otp', methods=['POST'])
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
    sender_email = "gautam.gs712@gmail.com"
    sender_password = "bigv rqeo incb dcht"

    # Call the send_email_otp function
    if send_email_otp(sender_email, sender_password, recipient_email, otp_subject, otp_body):
        return jsonify({'message': 'OTP sent successfully'}), 200
    else:
        return jsonify({'message': 'Failed to send OTP'}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    # Extract data from the POST request
    data = request.json
    user_otp = data.get('otp')

    # Check if the OTP matches
    if 'otp' in session and session['otp'] == user_otp:
        session.pop('otp', None)  # Remove OTP from session after verification
        return jsonify({'message': 'OTP verified successfully'}), 200
    else:
        return jsonify({'message': 'Invalid OTP'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
