# Medication Tracker App

A comprehensive web application designed to help individuals manage their medication regimens. This application enables users to track medication schedules, log adherence, and store important information about their prescriptions, including images of medications.

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Live Demo](#live-demo)
4. [Technology Stack](#technology-stack)
5. [AWS Integration](#aws-integration)
6. [Installation](#installation)
7. [Environment Setup](#environment-setup)
8. [Usage](#usage)
9. [Project Structure](#project-structure)
10. [Screenshots](#screenshots)
11. [Future Enhancements](#future-enhancements)

## Introduction

**Medication Tracker** helps users maintain their medication regimens by:
* **Tracking Medications**: Easily add, edit, and delete medication information.
* **Logging Adherence**: Record when medications are taken or missed.
* **Storing Images**: Upload and view images of medications for easy identification.
* **Custom Instructions**: Add specific instructions for how medications should be taken.

## Features

* **User Authentication System**
  * Secure registration and login functionality
  * Password protection for sensitive health information

* **Medication Management**
  * Add, edit, and delete medications
  * Record essential details (name, dosage, frequency, start/end dates)
  * Customize how medications should be taken (with meals, before meals, etc.)
  * Add custom instructions for special medication requirements
  * Upload and view medication images

* **Adherence Tracking**
  * Mark medications as taken or missed
  * View today's medication schedule on a dashboard
  * Track adherence history

* **Responsive Design**
  * Mobile-friendly interface
  * Bootstrap CSS framework for clean, modern styling

## Live Demo

You can view a live demo of the application at: http://34.226.193.61

## Technology Stack

* **Backend**
  * Python 3.x
  * Flask web framework
  * SQLAlchemy ORM
  * Werkzeug security utilities

* **Frontend**
  * HTML/CSS/JavaScript
  * Bootstrap 5
  * Jinja2 templating

* **Database**
  * MySQL (AWS RDS)
  * SQLite (local development)

* **Cloud Services**
  * AWS EC2 (application hosting)
  * AWS RDS (database service)
  * AWS S3 (image storage)
  
* **Web Server**
  * Nginx
  * Gunicorn

## AWS Integration

This application leverages several AWS services:

* **EC2**: Hosts the Flask application with Nginx and Gunicorn
* **RDS MySQL**: Stores application data in a managed database service
* **S3**: Handles secure storage and delivery of medication images

## Installation

### Prerequisites
* Python 3.x
* Git
* MySQL (for production) or SQLite (for development)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Medication-Tracker-App.git
cd Medication-Tracker-App
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Environment Setup

1. Create a `.env` file in the root directory:
```
DB_USER=your_database_username
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
S3_BUCKET=your_s3_bucket_name
S3_KEY=your_aws_access_key
S3_SECRET=your_aws_secret_key
```

2. For local development, you can use SQLite by modifying the database URI in app.py.

## Usage

1. Start the application:
```bash
python app.py
```

2. Access the application in your browser:
```
http://127.0.0.1:5000
```

### User Flow

1. **Registration**: Create a new account with username, email, and password
2. **Login**: Access your personal dashboard
3. **Dashboard**: View today's medications and their status
4. **Medication Management**: Add new medications, edit existing ones, or remove medications
5. **Tracking**: Mark medications as taken or missed from the dashboard

## Project Structure

```
medication-tracker/
├── app.py                  # Main Flask application
├── .env                    # Environment variables (not in repository)
├── .env.example            # Example environment variables template
├── requirements.txt        # Python dependencies
├── static/                 # Static files (CSS, JS)
│   ├── styles.css          # Custom styling
│   └── uploads/            # Local image uploads (dev only)
└── templates/              # HTML templates
    ├── add_medication.html # Form to add medications
    ├── base.html           # Base template with navigation
    ├── dashboard.html      # User dashboard
    ├── edit_medication.html # Form to edit medications
    ├── index.html          # Landing page
    ├── login.html          # Login form
    ├── medications.html    # List of medications
    └── register.html       # Registration form
```

## Future Enhancements

* Mobile application integration
* Medication reminders via email or SMS
* Interaction checking between medications
* Pharmacy integration for automatic refills
* Health provider sharing capabilities
* Analytics dashboard for adherence patterns

---

This project was developed as part of the CloudBerry Python Developer Training Program capstone project.
