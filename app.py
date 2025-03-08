from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key in production

# Database configuration - SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medication_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    medications = db.relationship('Medication', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    time_of_day = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)  # Path to locally stored image
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    logs = db.relationship('MedicationLog', backref='medication', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MedicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    taken_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    taken = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)

# Local file upload function (replaces S3)
def save_file_locally(file):
    """Save a file to local storage and return the path"""
    if not file:
        return None
        
    # Create uploads directory if it doesn't exist
    upload_folder = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}-{filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    try:
        file.save(file_path)
        # Return the relative path for database storage
        return f"uploads/{unique_filename}"
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user_exists = User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first()
        if user_exists:
            flash('Username or email already exists!')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    today = date.today()
    todays_medications = []
    
    for med in user.medications:
        if med.start_date <= today and (med.end_date is None or med.end_date >= today):
            # Check if medication has been taken today
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            today_log = MedicationLog.query.filter(
                MedicationLog.medication_id == med.id,
                MedicationLog.taken_at >= today_start,
                MedicationLog.taken_at <= today_end
            ).first()
            
            todays_medications.append({
                'medication': med,
                'taken': today_log.taken if today_log else None
            })
    
    return render_template('dashboard.html', medications=todays_medications, user=user)

@app.route('/medications')
def list_medications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    medications = Medication.query.filter_by(user_id=user.id).all()
    
    return render_template('medications.html', medications=medications)

@app.route('/medications/add', methods=['GET', 'POST'])
def add_medication():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        dosage = request.form['dosage']
        frequency = request.form['frequency']
        time_of_day = request.form['time_of_day']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None
        notes = request.form['notes']
        
        # Handle image upload locally
        image_path = None
        if 'medication_image' in request.files and request.files['medication_image'].filename:
            file = request.files['medication_image']
            image_path = save_file_locally(file)
        
        new_medication = Medication(
            name=name,
            dosage=dosage,
            frequency=frequency,
            time_of_day=time_of_day,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            image_path=image_path,
            user_id=session['user_id']
        )
        
        db.session.add(new_medication)
        db.session.commit()
        
        flash('Medication added successfully!')
        return redirect(url_for('list_medications'))
    
    return render_template('add_medication.html')

@app.route('/medications/log/<int:medication_id>/<string:status>')
def log_medication(medication_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    medication = Medication.query.get_or_404(medication_id)
    
    # Verify this medication belongs to the current user
    if medication.user_id != session['user_id']:
        flash('Unauthorized access!')
        return redirect(url_for('dashboard'))
    
    taken = True if status == 'taken' else False
    
    log = MedicationLog(
        medication_id=medication_id,
        taken=taken,
        taken_at=datetime.now()
    )
    
    db.session.add(log)
    db.session.commit()
    
    flash(f'Medication marked as {"taken" if taken else "missed"}!')
    return redirect(url_for('dashboard'))

@app.route('/medications/edit/<int:id>', methods=['GET', 'POST'])
def edit_medication(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    medication = Medication.query.get_or_404(id)
    
    # Verify this medication belongs to the current user
    if medication.user_id != session['user_id']:
        flash('Unauthorized access!')
        return redirect(url_for('list_medications'))
    
    if request.method == 'POST':
        medication.name = request.form['name']
        medication.dosage = request.form['dosage']
        medication.frequency = request.form['frequency']
        medication.time_of_day = request.form['time_of_day']
        medication.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        medication.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None
        medication.notes = request.form['notes']
        
        # Handle image upload
        if 'medication_image' in request.files and request.files['medication_image'].filename:
            file = request.files['medication_image']
            image_path = save_file_locally(file)
            if image_path:
                medication.image_path = image_path
        
        db.session.commit()
        flash('Medication updated successfully!')
        return redirect(url_for('list_medications'))
    
    return render_template('edit_medication.html', medication=medication)

@app.route('/medications/delete/<int:id>')
def delete_medication(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    medication = Medication.query.get_or_404(id)
    
    # Verify this medication belongs to the current user
    if medication.user_id != session['user_id']:
        flash('Unauthorized access!')
        return redirect(url_for('list_medications'))
    
    # Delete associated logs
    MedicationLog.query.filter_by(medication_id=id).delete()
    
    db.session.delete(medication)
    db.session.commit()
    
    flash('Medication deleted successfully!')
    return redirect(url_for('list_medications'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)