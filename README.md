# Hospital Management System (Healthcare AWS)

A modern, responsive healthcare administration web application built with **Python, Flask, SQLite, and Amazon Web Services (AWS S3 with Boto3)**. Designed for hospital staff and administrators with visual styling inspired by enterprise healthcare ERP systems (Navy blue sidebar, teal accents, clean typography, rounded cards, and subtle shadows).

---

## Key Features

- **Executive Dashboard**: Real-time KPI statistics cards (**28 Patients**, **8 Doctors**, **15 Appointments**, **5 Pending Appointments**), interactive Chart.js appointments overview line graph, and recent appointments feed.
- **Patient Management (`/patients`)**: Filterable and searchable patient directory with full demographic details, medical history, age, gender, contact information, and appointment tracking.
- **Doctor Directory (`/doctors`)**: Multi-column medical professional directory cards with doctor avatars, specialties (Cardiology, Pediatrics, Orthopedics, Neurology, etc.), qualifications, consultation hours, and profile views.
- **Appointment Booking (`/appointments/book`)**: Split booking interface with a patient & doctor slot scheduler alongside an interactive "Available Doctors" quick-selection sidebar.
- **Appointment Management (`/appointments`)**: Status filtering (Confirmed, Pending, Completed, Cancelled), quick status changer dropdown, and cancellation actions.
- **Amazon S3 Database Backup (`/backup`)**:
  - Performs atomic, non-locking SQLite database snapshots to `backups/hospital_backup_YYYYMMDD_HHMMSS.db`.
  - Connects to Amazon S3 via **Boto3** using the AWS default credential chain (supporting **EC2 IAM Roles** with zero hardcoded credentials).
  - Enforces **Server-Side Encryption (AES256)** and adheres to AWS **Block Public Access** standards.
  - Allows local download of database snapshots directly from the web interface.
  - Built-in diagnostic connectivity checker in Settings.
- **Settings & Demo Reset (`/settings`)**:
  - Admin profile management and secure password hashing via Werkzeug.
  - AWS configuration panel with live AJAX "Test S3 Connection" button.
  - One-click **"Reset Presentation Sample Data"** tool to restore the exact 28 patients, 8 doctors, and 15 appointments between college demonstration sessions.

---

## Visual Design System

| Element | Specification |
| :--- | :--- |
| **Sidebar** | Deep Navy Blue (`#0c1829`), crisp text, glowing cyan/teal active navigation pill |
| **Accents** | Teal Gradient (`#0891b2` to `#0d9488`), Cyan (`#06b6d4`) |
| **Background** | Clean Soft Gray (`#f8fafc`) with crisp white card containers |
| **Cards & Shadows** | Rounded corners (`12px` - `14px`), subtle soft shadows (`rgba(0, 0, 0, 0.05)`) |
| **Status Badges** | Green (Confirmed), Amber (Pending), Blue (Completed), Rose (Cancelled) |
| **Typography** | Inter (Google Fonts) with clear visual hierarchy |

---

## Windows Quickstart (Local Run)

The application is fully configured and ready to run locally on Windows.

### Method 1: Double-Click Launcher (Easiest)
1. Double-click **`run.bat`** in the project folder.
2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Method 2: PowerShell
Open PowerShell in this directory and execute:
```powershell
.\run.ps1
```

### Method 3: Manual Command Line
```powershell
# Activate virtual environment
.venv\Scripts\activate

# Launch Flask Server
python app.py
```

### Default Credentials
- **URL**: `http://localhost:5000/login`
- **Username**: `admin`
- **Password**: `admin123`
*(A "Fill Demo" button is provided on the login page for convenience during presentations!)*

---

## Running Automated Tests

Run the included unit test suite to verify all endpoints, database queries, and forms:
```powershell
.venv\Scripts\python.exe -m unittest test_app.py
```
*(All 8 test suites verify authentication, patients, doctors, appointments, S3 backup, and settings).*

---

## AWS Cloud Deployment Architecture (EC2 & S3)

When you are ready to deploy to AWS, follow this cost-effective, secure architecture:

```
+-------------------------------------------------------------+
|                         AWS Cloud                           |
|                                                             |
|   +--------------------------+     (Atomic Snapshots)       |
|   |       Amazon EC2         | ------------------------+    |
|   |  - Amazon Linux / Ubuntu |                         |    |
|   |  - Gunicorn + Nginx      |                         v    |
|   |  - Flask + SQLite        |               +--------------+
|   |  - IAM Role (Attached)   |               |  Amazon S3   |
|   +--------------------------+               | Private Bucket
|                |                             | Block Public |
|                v                             | Access ON    |
|      EC2 Instance Metadata (IMDS)            | SSE-AES256   |
|      (Temporary STS Credentials)             +--------------+
+-------------------------------------------------------------+
```

### Security Best Practices Implemented
1. **Zero Hardcoded Credentials**:
   - `boto3.client('s3')` automatically resolves credentials via the EC2 Instance Metadata Service (IMDS).
   - No AWS Access Keys (`AKIA...`) or Secret Keys are committed to code or stored on the filesystem.
2. **Private S3 Bucket**:
   - All backups are uploaded with default private ACLs.
   - S3 Bucket **Block Public Access** is kept enabled across all 4 AWS settings.
3. **Encryption at Rest**:
   - S3 uploads enforce `ServerSideEncryption: "AES256"`.
4. **Resilient Local Fallback**:
   - When running locally without AWS credentials, backups are safely created and preserved in the local `backups/` directory without crashing.

### Future EC2 Deployment Steps (When Approved)
1. **Create an S3 Bucket**:
   - Name: `hospital-backups-<your-unique-id>`
   - Region: `ap-south-1` (Mumbai) or your chosen region.
   - Keep "Block *all* public access" checked.
2. **Create an IAM Role for EC2**:
   - Attach an inline policy:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "s3:PutObject",
             "s3:GetObject",
             "s3:ListBucket"
           ],
           "Resource": [
             "arn:aws:s3:::hospital-backups-<your-unique-id>",
             "arn:aws:s3:::hospital-backups-<your-unique-id>/*"
           ]
         }
       ]
     }
     ```
3. **Launch a t2.micro / t3.micro EC2 Instance** (AWS Free Tier eligible).
4. **Attach the IAM Role** to the EC2 instance via *Actions -> Security -> Modify IAM role*.
5. **Update `.env`**:
   ```env
   S3_BUCKET_NAME=hospital-backups-<your-unique-id>
   AWS_DEFAULT_REGION=ap-south-1
   ```
6. **Run with Gunicorn & Nginx** for production-grade serving.

---

## Project Structure

```
hospital-management-aws/
│
├── .env                  # Environment configuration
├── .env.example          # Environment template
├── config.py             # Configuration loader
├── database.py           # SQLite schema & CRUD functions
├── seed_data.py          # 28 patients, 8 doctors, 15 appointments
├── s3_backup.py          # Safe SQLite snapshotting & Boto3 S3 upload
├── app.py                # Flask routes & controllers
├── test_app.py           # Automated test suite
├── run.bat               # Windows double-click launcher
├── run.ps1               # PowerShell launcher
├── requirements.txt      # Python dependencies
│
├── static/
│   ├── css/
│   │   └── style.css     # Design system (navy sidebar, teal accents)
│   ├── js/
│   │   └── app.js        # Front-end interactivity & AJAX
│   └── images/
│       └── hospital-bg.jpg # Exterior visual asset
│
├── templates/
│   ├── base.html         # Persistent sidebar & top navigation
│   ├── login.html        # Screen 1: Split login page
│   ├── dashboard.html    # Screen 2: Stats cards & charts
│   ├── patients.html     # Screen 3: Searchable patients list
│   ├── patient_form.html # Screen 7: Add/Edit patient form
│   ├── patient_detail.html # Patient profile & history
│   ├── doctors.html      # Screen 4: 3-column doctor cards grid
│   ├── doctor_form.html  # Add/Edit doctor form
│   ├── doctor_detail.html# Doctor profile details
│   ├── appointments.html # Screen 6: Appointment management
│   ├── book_appointment.html # Screen 5: Split booking page
│   ├── backup.html       # Screen 8: S3 backup dashboard
│   └── settings.html     # Screen 9: Tabbed administration
│
└── backups/              # Generated timestamped database backups
```

---

## License & Presentation Notice
This application uses **100% fictional sample data** for college presentation and portfolio demonstration purposes. No real patient health information (PHI) is stored.
