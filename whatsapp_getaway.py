from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

app = Flask(__name__)

# Your Twilio Account SID and Auth Token
ACCOUNT_SID = 'AC1af84a1009b422795b581eabd435361d'
AUTH_TOKEN = '78d805d82a9fe135ad3e9ffc34d8ac51'
TWILIO_PHONE_NUMBER = 'whatsapp:+13256664471'  # Twilio Sandbox WhatsApp number

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
