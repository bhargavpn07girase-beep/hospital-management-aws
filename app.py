import os
import functools
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
import database
import s3_backup
import seed_data

app = Flask(__name__)
app.config.from_object(Config)

# ----------------- Authentication Helpers -----------------

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access the hospital management dashboard.", "warning")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_global_data():
    """Inject common variables into all templates (user info, current path, settings)."""
    return {
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username', 'Admin'),
            'full_name': session.get('full_name', 'Administrator'),
            'role': session.get('role', 'Administrator')
        },
        's3_bucket': Config.S3_BUCKET_NAME,
        'aws_region': Config.AWS_REGION
    }

# ----------------- Auth Routes -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = database.get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('login'))

# ----------------- Dashboard Route -----------------

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    stats = database.get_dashboard_stats()
    recent_appointments = database.get_recent_appointments(limit=5)
    return render_template(
        'dashboard.html',
        stats=stats,
        recent_appointments=recent_appointments,
        active_page='dashboard'
    )

@app.route('/api/stats')
@login_required
def api_stats():
    stats = database.get_dashboard_stats()
    return jsonify(stats)

# ----------------- Patients Routes -----------------

@app.route('/patients')
@login_required
def patients():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    total_count = database.count_patients(query=query if query else None)
    patient_list = database.get_all_patients(query=query if query else None, limit=per_page, offset=offset)
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return render_template(
        'patients.html',
        patients=patient_list,
        query=query,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        active_page='patients'
    )

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', 'Male')
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        medical_history = request.form.get('medical_history', '').strip()

        if not full_name or not age or not phone:
            flash("Full Name, Age, and Phone Number are required fields.", "danger")
            return render_template('patient_form.html', action='Add', patient={}, active_page='patients')

        try:
            age_int = int(age)
            new_id = database.add_patient(
                full_name=full_name,
                age=age_int,
                gender=gender,
                phone=phone,
                email=email,
                address=address,
                medical_history=medical_history
            )
            flash(f"Patient '{full_name}' added successfully!", "success")
            return redirect(url_for('patients'))
        except Exception as e:
            flash(f"Error adding patient: {str(e)}", "danger")

    return render_template('patient_form.html', action='Add', patient={}, active_page='patients')

@app.route('/patients/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = database.get_patient_by_id(patient_id)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for('patients'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', 'Male')
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        medical_history = request.form.get('medical_history', '').strip()

        if not full_name or not age or not phone:
            flash("Full Name, Age, and Phone are required.", "danger")
            return render_template('patient_form.html', action='Edit', patient=patient, active_page='patients')

        try:
            database.update_patient(
                patient_id=patient_id,
                full_name=full_name,
                age=int(age),
                gender=gender,
                phone=phone,
                email=email,
                address=address,
                medical_history=medical_history
            )
            flash(f"Patient details for '{full_name}' updated successfully.", "success")
            return redirect(url_for('patients'))
        except Exception as e:
            flash(f"Error updating patient: {str(e)}", "danger")

    return render_template('patient_form.html', action='Edit', patient=patient, active_page='patients')

@app.route('/patients/view/<int:patient_id>')
@login_required
def view_patient(patient_id):
    patient = database.get_patient_by_id(patient_id)
    if not patient:
        flash("Patient record not found.", "danger")
        return redirect(url_for('patients'))
    appointments = database.get_patient_appointments(patient_id)
    return render_template('patient_detail.html', patient=patient, appointments=appointments, active_page='patients')

@app.route('/patients/delete/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = database.get_patient_by_id(patient_id)
    if patient:
        database.delete_patient(patient_id)
        flash(f"Patient record '{patient['full_name']}' ({patient['patient_code']}) deleted.", "info")
    return redirect(url_for('patients'))

# ----------------- Doctors Routes -----------------

@app.route('/doctors')
@login_required
def doctors():
    query = request.args.get('q', '').strip()
    department = request.args.get('dept', 'All')
    all_doctors = database.get_all_doctors(query=query if query else None, department=department if department != 'All' else None)

    return render_template(
        'doctors.html',
        doctors=all_doctors,
        query=query,
        selected_dept=department,
        active_page='doctors'
    )

@app.route('/doctors/add', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        specialty = request.form.get('specialty', '').strip()
        qualification = request.form.get('qualification', '').strip()
        department = request.form.get('department', '').strip()
        experience = request.form.get('experience', 5)
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        consulting_hours = request.form.get('consulting_hours', '09:00 AM - 05:00 PM')

        if not full_name or not specialty or not department:
            flash("Doctor Name, Specialty, and Department are required.", "danger")
            return render_template('doctor_form.html', action='Add', doctor={}, active_page='doctors')

        try:
            database.add_doctor(
                full_name=full_name,
                specialty=specialty,
                qualification=qualification,
                department=department,
                experience=int(experience),
                phone=phone,
                email=email,
                consulting_hours=consulting_hours
            )
            flash(f"Doctor '{full_name}' added to hospital directory.", "success")
            return redirect(url_for('doctors'))
        except Exception as e:
            flash(f"Error adding doctor: {str(e)}", "danger")

    return render_template('doctor_form.html', action='Add', doctor={}, active_page='doctors')

@app.route('/doctors/view/<int:doctor_id>')
@login_required
def view_doctor(doctor_id):
    doctor = database.get_doctor_by_id(doctor_id)
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for('doctors'))
    return render_template('doctor_detail.html', doctor=doctor, active_page='doctors')

@app.route('/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    doctor = database.get_doctor_by_id(doctor_id)
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for('doctors'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        specialty = request.form.get('specialty', '').strip()
        qualification = request.form.get('qualification', '').strip()
        department = request.form.get('department', '').strip()
        experience = request.form.get('experience', 5)
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        consulting_hours = request.form.get('consulting_hours', '09:00 AM - 05:00 PM')

        try:
            database.update_doctor(
                doctor_id=doctor_id,
                full_name=full_name,
                specialty=specialty,
                qualification=qualification,
                department=department,
                experience=int(experience),
                phone=phone,
                email=email,
                consulting_hours=consulting_hours
            )
            flash(f"Doctor details for '{full_name}' updated successfully.", "success")
            return redirect(url_for('doctors'))
        except Exception as e:
            flash(f"Error updating doctor: {str(e)}", "danger")

    return render_template('doctor_form.html', action='Edit', doctor=doctor, active_page='doctors')

@app.route('/doctors/delete/<int:doctor_id>', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    doctor = database.get_doctor_by_id(doctor_id)
    if doctor:
        database.delete_doctor(doctor_id)
        flash(f"Doctor record '{doctor['full_name']}' removed from staff directory.", "info")
    return redirect(url_for('doctors'))

# ----------------- Appointments Routes -----------------

@app.route('/appointments')
@login_required
def appointments():
    status = request.args.get('status', 'All')
    doctor_id = request.args.get('doctor_id', 'All')
    query = request.args.get('q', '').strip()

    all_appointments = database.get_all_appointments(
        status=status,
        doctor_id=doctor_id,
        query=query if query else None
    )
    doctors_list = database.get_all_doctors()

    return render_template(
        'appointments.html',
        appointments=all_appointments,
        doctors=doctors_list,
        selected_status=status,
        selected_doctor=doctor_id,
        query=query,
        active_page='appointments'
    )

@app.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason', '').strip()

        if not patient_id or not doctor_id or not appointment_date or not appointment_time:
            flash("Please fill in all required fields (Patient, Doctor, Date, and Time).", "danger")
        else:
            try:
                new_app_id = database.create_appointment(
                    patient_id=int(patient_id),
                    doctor_id=int(doctor_id),
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    reason=reason,
                    status='Confirmed'
                )
                flash("Appointment successfully scheduled!", "success")
                return redirect(url_for('appointments'))
            except Exception as e:
                flash(f"Error booking appointment: {str(e)}", "danger")

    patients_list = database.get_all_patients(limit=100)
    doctors_list = database.get_all_doctors()

    return render_template(
        'book_appointment.html',
        patients=patients_list,
        doctors=doctors_list,
        active_page='appointments'
    )

@app.route('/appointments/update-status/<int:appointment_id>', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    new_status = request.form.get('status')
    if new_status in ['Confirmed', 'Pending', 'Completed', 'Cancelled']:
        database.update_appointment_status(appointment_id, new_status)
        flash(f"Appointment status updated to '{new_status}'.", "success")
    return redirect(url_for('appointments'))

@app.route('/appointments/delete/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    database.delete_appointment(appointment_id)
    flash("Appointment record removed.", "info")
    return redirect(url_for('appointments'))

# ----------------- S3 Backup Routes -----------------

@app.route('/backup')
@login_required
def backup():
    backup_logs = database.get_all_backups()
    last_backup = database.get_last_backup()
    s3_info = {
        'bucket': Config.S3_BUCKET_NAME,
        'region': Config.AWS_REGION,
        'prefix': Config.S3_BACKUP_PREFIX,
        'access': 'Private (Public Access Blocked)'
    }
    return render_template(
        'backup.html',
        backups=backup_logs,
        last_backup=last_backup,
        s3_info=s3_info,
        active_page='backup'
    )

@app.route('/backup/create', methods=['POST'])
@login_required
def trigger_backup():
    try:
        result = s3_backup.perform_database_backup()
        if result['is_s3_uploaded']:
            flash(f"Success! Database backup '{result['filename']}' ({result['file_size_kb']} KB) created and securely uploaded to Amazon S3 bucket '{result['bucket']}'.", "success")
        else:
            flash(f"Database backup '{result['filename']}' ({result['file_size_kb']} KB) saved safely to local disk. {result['message']}", "info")
    except Exception as e:
        flash(f"Backup operation encountered an error: {str(e)}", "danger")

    return redirect(url_for('backup'))

@app.route('/backup/download/<path:filename>')
@login_required
def download_backup(filename):
    # Protect against directory traversal
    safe_filename = os.path.basename(filename)
    return send_from_directory(
        directory=str(Config.BACKUP_DIR),
        path=safe_filename,
        as_attachment=True
    )

# ----------------- Settings Routes -----------------

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = database.get_user_by_id(session['user_id'])
    last_backup = database.get_last_backup()
    return render_template(
        'settings.html',
        user=user,
        last_backup=last_backup,
        s3_bucket=Config.S3_BUCKET_NAME,
        aws_region=Config.AWS_REGION,
        s3_prefix=Config.S3_BACKUP_PREFIX,
        active_page='settings'
    )

@app.route('/settings/profile', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()

    if not full_name or not email:
        flash("Full name and email are required.", "danger")
    else:
        database.update_user_profile(session['user_id'], full_name, email)
        session['full_name'] = full_name
        flash("Profile updated successfully.", "success")

    return redirect(url_for('settings'))

@app.route('/settings/security', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    user = database.get_user_by_id(session['user_id'])
    if not check_password_hash(user['password_hash'], current_password):
        flash("Incorrect current password.", "danger")
    elif len(new_password) < 6:
        flash("New password must be at least 6 characters.", "danger")
    elif new_password != confirm_password:
        flash("New passwords do not match.", "danger")
    else:
        new_hash = generate_password_hash(new_password)
        database.update_user_password(session['user_id'], new_hash)
        flash("Password updated successfully.", "success")

    return redirect(url_for('settings'))

@app.route('/settings/test-s3', methods=['POST'])
@login_required
def test_s3_ajax():
    result = s3_backup.test_s3_connection()
    return jsonify(result)

@app.route('/settings/reset-data', methods=['POST'])
@login_required
def reset_demo_data():
    """Reset to sample presentation data."""
    try:
        conn = database.get_db_connection()
        conn.execute("DELETE FROM appointments")
        conn.execute("DELETE FROM patients")
        conn.execute("DELETE FROM doctors")
        conn.commit()
        conn.close()

        seed_data.seed_database()
        flash("Presentation sample data successfully reset and re-seeded!", "success")
    except Exception as e:
        flash(f"Error resetting data: {str(e)}", "danger")

    return redirect(url_for('dashboard'))

# ----------------- Main Entrypoint -----------------

if __name__ == '__main__':
    database.init_db()
    seed_data.seed_database()
    print("=" * 60)
    print(" Hospital Management System is running!")
    print(f" Local Web Interface: http://localhost:{Config.PORT}")
    print(f" Admin Credentials  : Username: admin | Password: admin123")
    print("=" * 60)
    app.run(host='0.0.0.0', port=Config.PORT, debug=True)
