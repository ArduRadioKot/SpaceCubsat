from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
import json
import serial
import threading
import time
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Global variables for telemetry
telemetry_data = {}
telemetry_lock = threading.Lock()

# Login required decorator for admin only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['username'] != ADMIN_USERNAME:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Serial communication with Arduino
def read_telemetry():
    """Read telemetry data from Arduino via serial/UART"""
    try:
        # Try different serial ports
        ports = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/tty.usbserial-1410', 'COM3']
        ser = None
        
        for port in ports:
            try:
                ser = serial.Serial(port, 9600, timeout=1)
                print(f"Connected to Arduino on {port}")
                break
            except serial.SerialException:
                continue
        
        if not ser:
            print("Arduino not found. Using simulated data.")
            simulate_telemetry()
            return
        
        while True:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        parse_telemetry_line(line)
                time.sleep(0.1)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
            except Exception as e:
                print(f"Error reading telemetry: {e}")
                break
        
        if ser:
            ser.close()
            
    except Exception as e:
        print(f"Telemetry error: {e}")
        simulate_telemetry()

def simulate_telemetry():
    """Simulate telemetry data when Arduino is not connected"""
    import random
    
    while True:
        with telemetry_lock:
            telemetry_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'satellite_id': random.randint(1, 6),
                'temperature': round(random.uniform(-20, 50), 2),
                'battery': round(random.uniform(3.0, 4.2), 2),
                'signal_strength': round(random.uniform(-80, -30), 2),
                'altitude': round(random.uniform(480, 600), 2),
                'speed': round(random.uniform(7.5, 7.8), 2),
                'status': random.choice(['Active', 'Inactive', 'Maintenance'])
            }
        time.sleep(5)

def parse_telemetry_line(line):
    """Parse telemetry data from Arduino"""
    try:
        # Expected format: ID:1,T:25.5,B:3.7,S:-45,A:520,V:7.6,STATUS:Active
        parts = line.split(',')
        data = {}
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                if key == 'ID':
                    data['satellite_id'] = int(value)
                elif key == 'T':
                    data['temperature'] = float(value)
                elif key == 'B':
                    data['battery'] = float(value)
                elif key == 'S':
                    data['signal_strength'] = float(value)
                elif key == 'A':
                    data['altitude'] = float(value)
                elif key == 'V':
                    data['speed'] = float(value)
                elif key == 'STATUS':
                    data['status'] = value
        
        data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        with telemetry_lock:
            telemetry_data.update(data)
            
    except Exception as e:
        print(f"Error parsing telemetry: {e}")

# Load satellite data from JSON file
def load_satellites():
    try:
        with open('satellites.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default data if file doesn't exist or is invalid
        default_data = [
            {
                'id': 1,
                'name': 'SITeye-1',
                'status': 'Active',
                'launch_date': '2026-01-27',
                'mission': 'Сеть дистанционного зондирования Земли',
                'altitude': '520 km',
                'last_contact': '2026-01-27 14:30:22',
                'description': 'Спутник дистанционного зондирования формата 1U',
                'image': '1.png',
                'owner': 'admin'
            },
            {
                'id': 2,
                'name': 'SITeye-2',
                'status': 'Active',
                'launch_date': '2026-01-27',
                'mission': 'Сеть дистанционного зондирования Земли',
                'altitude': '540 km',
                'last_contact': '2026-01-27 15:45:10',
                'description': 'Спутник дистанционного зондирования формата 1U',
                'image': '2.png',
                'owner': 'admin'
            },
            {
                'id': 3,
                'name': 'SITeye-3',
                'status': 'Maintenance',
                'launch_date': '2026-01-27',
                'mission': 'Сеть дистанционного зондирования Земли',
                'altitude': '510 km',
                'last_contact': '2026-01-25 09:20:15',
                'description': 'Спутник дистанционного зондирования формата 1U',
                'image': '3.png',
                'owner': 'user'
            },
            {
                'id': 4,
                'name': 'SITeye-4',
                'status': 'Active',
                'launch_date': '2026-01-27',
                'mission': 'Сеть дистанционного зондирования Земли',
                'altitude': '530 km',
                'last_contact': '2026-01-27 16:10:45',
                'description': 'Спутник дистанционного зондирования формата 1U',
                'image': '4.png',
                'owner': 'admin'
            },
            {
                'id': 5,
                'name': 'SITeye-5',
                'status': 'Inactive',
                'launch_date': '2026-01-27',
                'mission': 'Сеть дистанционного зондирования Земли',
                'altitude': '480 km',
                'last_contact': '2026-01-20 22:10:33',
                'description': 'Спутник дистанционного зондирования формата 1U',
                'image': '5.png',
                'owner': 'user'
            },
            {
                'id': 6,
                'name': 'SITeye-6',
                'status': 'Active',
                'launch_date': '2026-01-27',
                'mission': 'Сеть дистанционного зондирования Земли',
                'altitude': '510 km',
                'last_contact': '2026-01-27 10:05:17',
                'description': 'Спутник дистанционного зондирования формата 1U',
                'image': '6.png',
                'owner': 'admin'
            }
        ]
        with open('satellites.json', 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['username'] = username
            flash('Успешный вход как администратор', 'success')
            return redirect(url_for('dashboard'))
        flash('Неверные учетные данные администратора', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    username = session.get('username', 'guest')
    return render_template('dashboard.html', username=username)

@app.route('/profile')
def profile():
    username = session.get('username', 'guest')
    satellites = load_satellites()
    user_satellites = satellites  # All satellites visible to guest users
    return render_template('profile.html', 
                         username=username,
                         satellite_count=len(user_satellites),
                         active_satellites=sum(1 for s in user_satellites if s['status'] == 'Active'))

@app.route('/api/satellites')
def get_satellites():
    satellites = load_satellites()
    # All satellites visible to all users
    return jsonify(satellites)

@app.route('/satellite/<int:satellite_id>')
def satellite_detail(satellite_id):
    satellites = load_satellites()
    satellite = next((s for s in satellites if s['id'] == satellite_id), None)
    if not satellite:
        flash('Satellite not found', 'error')
        return redirect(url_for('dashboard'))
    return render_template('satellite_detail.html', satellite=satellite)

@app.route('/api/telemetry')
def get_telemetry():
    with telemetry_lock:
        return jsonify(telemetry_data)

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/api/configure-satellite', methods=['POST'])
@admin_required
def configure_satellite():
    try:
        data = request.get_json()
        satellite_id = data.get('satellite_id')
        rotation_x = data.get('rotation_x')
        rotation_y = data.get('rotation_y')
        rotation_z = data.get('rotation_z')
        
        # Here you would send the configuration commands to the Arduino
        # For now, we'll just log it
        print(f"Configuring satellite {satellite_id}: X={rotation_x}, Y={rotation_y}, Z={rotation_z}")
        
        # Send command to Arduino if connected
        command = f"CONFIG:{satellite_id}:X{rotation_x}:Y{rotation_y}:Z{rotation_z}"
        # You can add serial communication here if needed
        
        return jsonify({'status': 'success', 'message': 'Configuration applied successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/admin/satellites', methods=['GET', 'POST'])
@admin_required
def admin_satellites():
    if request.method == 'POST':
        # Update satellite data
        satellites = load_satellites()
        data = request.get_json()
        for sat in satellites:
            if sat['id'] == data.get('id'):
                sat.update(data)
                break
        with open('satellites.json', 'w') as f:
            json.dump(satellites, f, indent=2)
        return jsonify({'status': 'success'})
    
    satellites = load_satellites()
    return render_template('admin_satellites.html', satellites=satellites)

if __name__ == '__main__':
    # Ensure the static folder exists for serving static files
    os.makedirs('static', exist_ok=True)
    
    # Start telemetry reading thread
    telemetry_thread = threading.Thread(target=read_telemetry, daemon=True)
    telemetry_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
