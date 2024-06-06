from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
# Your Twilio Account SID and Auth Token
ACCOUNT_SID = os.getenv('ACCOUNT_SID')
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')  # Your Twilio phone number

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_getaway_message(to_phone_number, message_body):
    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        return {'status': 'Message sent', 'sid': message.sid}
    except TwilioRestException as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': 'An unexpected error occurred: ' + str(e)}

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    to_number = data.get('to')
    message_body = data.get('message')

    if not to_number or not message_body:
        return jsonify({'error': 'Missing "to" or "message" field'}), 400

    response = send_getaway_message(to_number, message_body)
    return jsonify(response), 200 if 'status' in response else 500

if __name__ == '__main__':
    app.run(debug=True)
