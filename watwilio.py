from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# Your Twilio Account SID and Auth Token
ACCOUNT_SID = os.getenv('ACCOUNT_SID')
AUTH_TOKEN = os.getenv('AUTH_TOKEN_WA')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER_WA')  # Twilio Sandbox WhatsApp number

client = Client(ACCOUNT_SID, AUTH_TOKEN)

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    to_number = data.get('to')
    message_body = data.get('message')

    if not to_number or not message_body:
        return jsonify({'error': 'Missing "to" or "message" field'}), 400

    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=f'whatsapp:{to_number}'
        )
        return jsonify({'status': 'Message sent', 'sid': message.sid}), 200
    except TwilioRestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
