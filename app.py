from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import os
import secrets
import bcrypt  # Untuk hashing password
import cv2
from ultralytics import YOLO
# Import model-related functions but do not initialize anything yet
from model import detect_and_track_cars

app = Flask(__name__)

# Generate a secret key
app.secret_key = secrets.token_hex(16)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dropoffzone'

mysql = MySQL(app)
app.config['UPLOAD_FOLDER'] = 'static/videos'

cap = None  # Global variable to hold video capture object
model = None  # Global variable to hold model

# Clear session on each request to ensure proper initialization
@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'videoFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['videoFile']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        global cap
        global model

        # Initialize video capture object
        cap = cv2.VideoCapture(input_path)  
        
        # Initialize the model if not already initialized
        if model is None:
            
            model = YOLO('model/031924.pt')

        return jsonify({'video_url': '/video_feed'}), 200

    return jsonify({'error': 'File processing failed'}), 500

def generate_frames():
    global cap
    if not cap.isOpened():
        return

    # Define the dropoff zone coordinates
    zone = [(690, 380), (750, 390), (640, 475), (530, 460)]

    # Set of active car IDs that are currently in the zone
    active_cars = set()

    # Dictionary to hold start time for each car
    timers = {}

    # Dictionary to track alarm status for each car
    alarms = {}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = detect_and_track_cars(frame, model, zone, active_cars, timers, alarms)

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    # Periksa jenis konten permintaan
    if request.headers['Content-Type'] == 'application/json':
        # Jika permintaan adalah JSON
        data = request.get_json()
        username = data['username']
        password = data['password']
    else:
        # Jika permintaan adalah form-urlencoded
        username = request.form['username']
        password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
        session['user'] = username
        flash('Login successful!', 'success')
        if request.is_json:
            return jsonify(message="Login successful!")
        else:
            return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password', 'danger')
        if request.is_json:
            return jsonify(error="Invalid username or password"), 401
        else:
            return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Periksa jenis konten permintaan
        if request.headers['Content-Type'] == 'application/json':
            # Jika permintaan adalah JSON
            data = request.get_json()
            username = data['username']
            nomer_wa = data['nomer_wa']
            password = data['password']
            repeat_password = data['repeat_password']
        else:
            # Jika permintaan adalah form-urlencoded
            username = request.form['username']
            nomer_wa = request.form['nomer_wa']
            password = request.form['password']
            repeat_password = request.form['repeat_password']

        if password != repeat_password:
            if request.headers['Content-Type'] == 'application/json':
                return jsonify(error='Passwords do not match'), 400  # Return JSON response with error message and status code
            else:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('register'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, nomer_wa, password) VALUES (%s, %s, %s)", 
                    (username, nomer_wa, hashed_password.decode('utf-8')))
        mysql.connection.commit()
        cur.close()
        
        if request.headers['Content-Type'] == 'application/json':
            return jsonify(message='You have successfully registered!'), 201  # Return JSON response with success message and status code
        else:
            flash('You have successfully registered!', 'success')
            return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/data')
def data():
    if 'user' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('index'))
    return render_template('laporan-trafik.html')

if __name__ == '__main__':
    app.run(debug=True)
