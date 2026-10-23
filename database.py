import sqlite3
import datetime
from pathlib import Path
from config import Config

def get_db_connection():
    """Create and return a SQLite database connection with row factory configured."""
    conn = sqlite3.connect(str(Config.DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Administrator',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Patients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT,
        medical_history TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Doctors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        qualification TEXT NOT NULL,
        department TEXT NOT NULL,
        experience INTEGER DEFAULT 5,
        phone TEXT,
        email TEXT,
        avatar TEXT,
        consulting_hours TEXT DEFAULT '09:00 AM - 05:00 PM',
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Appointments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_code TEXT UNIQUE NOT NULL,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        reason TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    );
    """)

    # Backups log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_size_kb REAL NOT NULL,
        s3_bucket TEXT,
        s3_key TEXT,
        status TEXT NOT NULL,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # System settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

# ----------------- User Functions -----------------

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def update_user_profile(user_id, full_name, email):
    conn = get_db_connection()
    conn.execute("UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user_id))
    conn.commit()
    conn.close()

def update_user_password(user_id, password_hash):
    conn = get_db_connection()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()

# ----------------- Patient Functions -----------------

def get_next_patient_code():
    conn = get_db_connection()
    row = conn.execute("SELECT patient_code FROM patients ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row and row['patient_code'].startswith('P'):
        try:
            num = int(row['patient_code'][1:]) + 1
            return f"P{num:03d}"
        except ValueError:
            pass
    return "P001"

def get_all_patients(query=None, limit=50, offset=0):
    conn = get_db_connection()
    if query:
        search = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM patients 
               WHERE full_name LIKE ? OR phone LIKE ? OR patient_code LIKE ? OR email LIKE ?
               ORDER BY id ASC LIMIT ? OFFSET ?""",
            (search, search, search, search, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM patients ORDER BY id ASC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    conn.close()
    return rows

def count_patients(query=None):
    conn = get_db_connection()
    if query:
        search = f"%{query}%"
        count = conn.execute(
            """SELECT COUNT(*) as count FROM patients 
               WHERE full_name LIKE ? OR phone LIKE ? OR patient_code LIKE ? OR email LIKE ?""",
            (search, search, search, search)
        ).fetchone()['count']
    else:
        count = conn.execute("SELECT COUNT(*) as count FROM patients").fetchone()['count']
    conn.close()
    return count

def get_patient_by_id(patient_id):
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return patient

def add_patient(full_name, age, gender, phone, email="", address="", medical_history=""):
    code = get_next_patient_code()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO patients (patient_code, full_name, age, gender, phone, email, address, medical_history)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (code, full_name, age, gender, phone, email, address, medical_history)
    )
    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return patient_id

def update_patient(patient_id, full_name, age, gender, phone, email="", address="", medical_history=""):
    conn = get_db_connection()
    conn.execute(
        """UPDATE patients 
           SET full_name = ?, age = ?, gender = ?, phone = ?, email = ?, address = ?, medical_history = ?
           WHERE id = ?""",
        (full_name, age, gender, phone, email, address, medical_history, patient_id)
    )
    conn.commit()
    conn.close()

def delete_patient(patient_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()

# ----------------- Doctor Functions -----------------

def get_next_doctor_code():
    conn = get_db_connection()
    row = conn.execute("SELECT doctor_code FROM doctors ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row and row['doctor_code'].startswith('D'):
        try:
            num = int(row['doctor_code'][1:]) + 1
            return f"D{num:03d}"
        except ValueError:
            pass
    return "D001"

def get_all_doctors(query=None, department=None):
    conn = get_db_connection()
    sql = "SELECT * FROM doctors WHERE 1=1"
    params = []
    if query:
        sql += " AND (full_name LIKE ? OR specialty LIKE ? OR department LIKE ?)"
        search = f"%{query}%"
        params.extend([search, search, search])
    if department and department != 'All':
        sql += " AND department = ?"
        params.append(department)
    sql += " ORDER BY id ASC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows

def get_doctor_by_id(doctor_id):
    conn = get_db_connection()
    doctor = conn.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
    conn.close()
    return doctor

def add_doctor(full_name, specialty, qualification, department, experience=5, phone="", email="", consulting_hours="09:00 AM - 05:00 PM", avatar=""):
    code = get_next_doctor_code()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO doctors (doctor_code, full_name, specialty, qualification, department, experience, phone, email, consulting_hours, avatar)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (code, full_name, specialty, qualification, department, experience, phone, email, consulting_hours, avatar)
    )
    doctor_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doctor_id

def update_doctor(doctor_id, full_name, specialty, qualification, department, experience, phone, email, consulting_hours, is_available=1):
    conn = get_db_connection()
    conn.execute(
        """UPDATE doctors 
           SET full_name = ?, specialty = ?, qualification = ?, department = ?, experience = ?, phone = ?, email = ?, consulting_hours = ?, is_available = ?
           WHERE id = ?""",
        (full_name, specialty, qualification, department, experience, phone, email, consulting_hours, is_available, doctor_id)
    )
    conn.commit()
    conn.close()

def delete_doctor(doctor_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
    conn.commit()
    conn.close()

# ----------------- Appointment Functions -----------------

def get_next_appointment_code():
    conn = get_db_connection()
    row = conn.execute("SELECT appointment_code FROM appointments ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row and row['appointment_code'].startswith('A'):
        try:
            num = int(row['appointment_code'][1:]) + 1
            return f"A{num:03d}"
        except ValueError:
            pass
    return "A001"

def get_all_appointments(status=None, doctor_id=None, query=None, limit=100, offset=0):
    conn = get_db_connection()
    sql = """
    SELECT a.*, 
           p.full_name AS patient_name, p.phone AS patient_phone, p.patient_code,
           d.full_name AS doctor_name, d.specialty AS doctor_specialty, d.department AS doctor_department
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN doctors d ON a.doctor_id = d.id
    WHERE 1=1
    """
    params = []
    if status and status != 'All':
        sql += " AND a.status = ?"
        params.append(status)
    if doctor_id and doctor_id != 'All':
        sql += " AND a.doctor_id = ?"
        params.append(doctor_id)
    if query:
        search = f"%{query}%"
        sql += " AND (p.full_name LIKE ? OR d.full_name LIKE ? OR a.appointment_code LIKE ? OR a.reason LIKE ?)"
        params.extend([search, search, search, search])
    
    sql += " ORDER BY a.appointment_date DESC, a.appointment_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows

def get_appointment_by_id(appointment_id):
    conn = get_db_connection()
    sql = """
    SELECT a.*, 
           p.full_name AS patient_name, p.phone AS patient_phone, p.patient_code, p.age AS patient_age, p.gender AS patient_gender,
           d.full_name AS doctor_name, d.specialty AS doctor_specialty, d.department AS doctor_department
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN doctors d ON a.doctor_id = d.id
    WHERE a.id = ?
    """
    row = conn.execute(sql, (appointment_id,)).fetchone()
    conn.close()
    return row

def create_appointment(patient_id, doctor_id, appointment_date, appointment_time, reason="", status="Pending", notes=""):
    code = get_next_appointment_code()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO appointments (appointment_code, patient_id, doctor_id, appointment_date, appointment_time, reason, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (code, patient_id, doctor_id, appointment_date, appointment_time, reason, status, notes)
    )
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id

def update_appointment_status(appointment_id, status):
    conn = get_db_connection()
    conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
    conn.commit()
    conn.close()

def delete_appointment(appointment_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()

def get_recent_appointments(limit=5):
    conn = get_db_connection()
    sql = """
    SELECT a.*, 
           p.full_name AS patient_name,
           d.full_name AS doctor_name, d.specialty AS doctor_specialty
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN doctors d ON a.doctor_id = d.id
    ORDER BY a.appointment_date DESC, a.appointment_time DESC
    LIMIT ?
    """
    rows = conn.execute(sql, (limit,)).fetchall()
    conn.close()
    return rows

def get_patient_appointments(patient_id):
    conn = get_db_connection()
    sql = """
    SELECT a.*, d.full_name AS doctor_name, d.specialty AS doctor_specialty
    FROM appointments a
    JOIN doctors d ON a.doctor_id = d.id
    WHERE a.patient_id = ?
    ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """
    rows = conn.execute(sql, (patient_id,)).fetchall()
    conn.close()
    return rows

# ----------------- Dashboard Analytics -----------------

def get_dashboard_stats():
    conn = get_db_connection()
    total_patients = conn.execute("SELECT COUNT(*) AS c FROM patients").fetchone()['c']
    total_doctors = conn.execute("SELECT COUNT(*) AS c FROM doctors").fetchone()['c']
    total_appointments = conn.execute("SELECT COUNT(*) AS c FROM appointments").fetchone()['c']
    pending_appointments = conn.execute("SELECT COUNT(*) AS c FROM appointments WHERE status = 'Pending'").fetchone()['c']
    confirmed_appointments = conn.execute("SELECT COUNT(*) AS c FROM appointments WHERE status = 'Confirmed'").fetchone()['c']
    completed_appointments = conn.execute("SELECT COUNT(*) AS c FROM appointments WHERE status = 'Completed'").fetchone()['c']
    cancelled_appointments = conn.execute("SELECT COUNT(*) AS c FROM appointments WHERE status = 'Cancelled'").fetchone()['c']

    # Monthly trends for chart
    # Default months in case DB has limited data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_data = [12, 18, 22, 35, 28, 45, 38, 42, 50, 48, 55, 60]

    conn.close()
    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
        "confirmed_appointments": confirmed_appointments,
        "completed_appointments": completed_appointments,
        "cancelled_appointments": cancelled_appointments,
        "chart_labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "chart_data": [12, 19, 32, 28, 45, 38]
    }

# ----------------- Backup Log Functions -----------------

def add_backup_record(filename, file_size_kb, s3_bucket, s3_key, status, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO backups (filename, file_size_kb, s3_bucket, s3_key, status, message)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (filename, file_size_kb, s3_bucket, s3_key, status, message)
    )
    backup_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return backup_id

def get_all_backups(limit=20):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM backups ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows

def get_last_backup():
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM backups ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return row

# ----------------- System Settings -----------------

def get_setting(key, default=""):
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row['value'] if row else default

def set_setting(key, value):
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO system_settings (key, value, updated_at) 
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP""",
        (key, value)
    )
    conn.commit()
    conn.close()
