from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
import secrets
import bcrypt  # Untuk hashing password

app = Flask(__name__)

# Generate a secret key
app.secret_key = secrets.token_hex(16)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dropoffzone'

mysql = MySQL(app)

# Clear session on each request to ensure proper initialization
@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

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
