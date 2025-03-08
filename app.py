from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import boto3
import uuid

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key in production

# Database configuration - this will be updated for RDS in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medication_tracker.db'  # Local development
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# AWS S3 configuration
app.config['S3_BUCKET'] = os.environ.get('S3_BUCKET', 'medication-tracker-files')
app.config['S3_KEY'] = os.environ.get('AWS_ACCESS_KEY_ID')
app.config['S3_SECRET'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
app.config['S3_REGION'] = os.environ.get('AWS_REGION', 'us-east-1')

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
    image_url = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    logs = db.relationship('MedicationLog', backref='medication', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MedicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    taken_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    taken = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)

# S3 helper function
def upload_file_to_s3(file):
    """Upload a file to S3 bucket and return the URL"""
    if not app.config['S3_KEY'] or not app.config['S3_SECRET']:
        # For local development without S3
        return None
    
    s3 = boto3.client(
        "s3",
        aws_access_key_id=app.config['S3_KEY'],
        aws_secret_access_key=app.config['S3_SECRET'],
        region_name=app.config['S3_REGION']
    )
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}-{filename}"
    
    try:
        s3.upload_fileobj(
            file,
            app.config['S3_BUCKET'],
            unique_filename,
            ExtraArgs={"ACL": "public-read", "ContentType": file.content_type}
        )
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None
        
    return f"https://{app.config['S3_BUCKET']}.s3.amazonaws.com/{unique_filename}"

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
            today_log = MedicationLog.query.filter_by(
                medication_id=med.id, 
                taken_at=datetime.now().strftime('%Y-%m-%d')
            ).first()
            
            todays_medications.append({
                'medication': med,
                'taken': today_log.taken if today_log else None
            })
    
    return render_template('dashboard.html', medications=todays_medications, user=user)

# Add more routes for medications CRUD operations
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
        
        # Handle image upload
        image_url = None
        if 'medication_image' in request.files and request.files['medication_image'].filename:
            file = request.files['medication_image']
            image_url = upload_file_to_s3(file)
        
        new_medication = Medication(
            name=name,
            dosage=dosage,
            frequency=frequency,
            time_of_day=time_of_day,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            image_url=image_url,
            user_id=session['user_id']
        )
        
        db.session.add(new_medication)
        db.session.commit()
        
        flash('Medication added successfully!')
        return redirect(url_for('list_medications'))
    
    return render_template('add_medication.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)