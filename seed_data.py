import sqlite3
from werkzeug.security import generate_password_hash
from database import init_db, get_db_connection

def seed_database():
    """Populate database with fictional sample data for college demonstration."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed Admin User
    admin_exists = cursor.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin_exists:
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, email, role)
               VALUES (?, ?, ?, ?, ?)""",
            ('admin', generate_password_hash('admin123'), 'Administrator', 'admin@hospital.com', 'Super Administrator')
        )

    # 2. Seed Doctors (8 doctors matching reference UI)
    doctors_count = cursor.execute("SELECT COUNT(*) as c FROM doctors").fetchone()['c']
    if doctors_count == 0:
        doctors_data = [
            ("D001", "Dr. Priya Singh", "Cardiologist", "MBBS, MD (Cardiology)", "Cardiology", 12, "9876543210", "priya.singh@hospital.com", "09:00 AM - 02:00 PM", "female-doctor-1"),
            ("D002", "Dr. Amit Kumar", "General Physician", "MBBS, MD (General Medicine)", "General Medicine", 10, "9876543211", "amit.kumar@hospital.com", "10:00 AM - 04:00 PM", "male-doctor-1"),
            ("D003", "Dr. Neha Joshi", "Pediatrician", "MBBS, MD (Pediatrics)", "Pediatrics", 8, "9876543212", "neha.joshi@hospital.com", "09:00 AM - 01:00 PM", "female-doctor-2"),
            ("D004", "Dr. Rakesh Mehta", "Orthopedist", "MBBS, MS (Orthopedics)", "Orthopedics", 15, "9876543213", "rakesh.mehta@hospital.com", "11:00 AM - 05:00 PM", "male-doctor-2"),
            ("D005", "Dr. Snehal Verma", "Gynecologist", "MBBS, MS (Obstetrics & Gynae)", "Gynecology", 9, "9876543214", "snehal.verma@hospital.com", "09:30 AM - 03:30 PM", "female-doctor-3"),
            ("D006", "Dr. Arjun Nair", "Dermatologist", "MBBS, MD (Dermatology)", "Dermatology", 7, "9876543215", "arjun.nair@hospital.com", "10:30 AM - 04:30 PM", "male-doctor-3"),
            ("D007", "Dr. Sunita Rao", "Neurologist", "MBBS, DM (Neurology)", "Neurology", 14, "9876543216", "sunita.rao@hospital.com", "08:30 AM - 01:30 PM", "female-doctor-4"),
            ("D008", "Dr. Rajesh Khanna", "Oncologist", "MBBS, MD, DM (Medical Oncology)", "Oncology", 16, "9876543217", "rajesh.khanna@hospital.com", "11:00 AM - 04:00 PM", "male-doctor-4")
        ]
        cursor.executemany(
            """INSERT INTO doctors (doctor_code, full_name, specialty, qualification, department, experience, phone, email, consulting_hours, avatar)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            doctors_data
        )

    # 3. Seed Patients (28 patients matching reference UI stats)
    patients_count = cursor.execute("SELECT COUNT(*) as c FROM patients").fetchone()['c']
    if patients_count == 0:
        patients_data = [
            ("P001", "Rahul Sharma", 32, "Male", "9876543210", "rahul.sharma@example.com", "Flat 402, Green Valley Apartments, Mumbai", "Mild hypertension, seasonal allergies"),
            ("P002", "Sneha Patel", 28, "Female", "8765432109", "sneha.patel@example.com", "Plot 12, Sunrise Residency, Pune", "No prior medical conditions"),
            ("P003", "Vikram Rao", 45, "Male", "7654321098", "vikram.rao@example.com", "88 Palm Meadows, Whitefield, Bangalore", "Type 2 Diabetes, controlled on diet"),
            ("P004", "Anita Desai", 36, "Female", "6543210987", "anita.desai@example.com", "A-14, Mayur Vihar Phase 1, New Delhi", "Post-surgical recovery, knee arthroscopy"),
            ("P005", "Karan Mehta", 50, "Male", "5432109876", "karan.mehta@example.com", "B-201, Shanti Heights, Ahmedabad", "Routine checkup, elevated cholesterol"),
            ("P006", "Pooja Verma", 29, "Female", "9811223344", "pooja.verma@example.com", "House 45, Jubilee Hills, Hyderabad", "Eczema and contact dermatitis"),
            ("P007", "Arjun Sharma", 41, "Male", "9822334455", "arjun.sharma@example.com", "12 Civil Lines, Jaipur", "Chronic sinus issues"),
            ("P008", "Neha Kapoor", 34, "Female", "9833445566", "neha.kapoor@example.com", "Sector 17-C, Chandigarh", "Frequent migraine headaches"),
            ("P009", "Rakesh Patel", 58, "Male", "9844556677", "rakesh.patel@example.com", "Ring Road, Surat", "Hypertension and mild lumbar pain"),
            ("P010", "Savitri Devi", 68, "Female", "9855667788", "savitri.devi@example.com", "Gomti Nagar, Lucknow", "Osteoarthritis in both knees"),
            ("P011", "Mohit Bansal", 25, "Male", "9866778899", "mohit.bansal@example.com", "Arera Colony, Bhopal", "Asthma since childhood"),
            ("P012", "Ananya Joshi", 22, "Female", "9877889900", "ananya.joshi@example.com", "Vijay Nagar, Indore", "Annual preventative checkup"),
            ("P013", "Suresh Nair", 61, "Male", "9888990011", "suresh.nair@example.com", "Marine Drive, Kochi", "Cardiac stent placed in 2023"),
            ("P014", "Meera Krishnan", 39, "Female", "9899001122", "meera.krishnan@example.com", "Anna Nagar, Chennai", "Hypothyroidism on levothyroxine"),
            ("P015", "Rajesh Gupta", 48, "Male", "9900112233", "rajesh.gupta@example.com", "Salt Lake Sector V, Kolkata", "Gastritis and acidity"),
            ("P016", "Kavita Reddy", 31, "Female", "9911223344", "kavita.reddy@example.com", "MVP Colony, Visakhapatnam", "Migraine trigger investigation"),
            ("P017", "Deepak Chawla", 53, "Male", "9922334455", "deepak.chawla@example.com", "Ramdaspeth, Nagpur", "Pre-diabetic management"),
            ("P018", "Priyanka Sen", 27, "Female", "9933445566", "priyanka.sen@example.com", "Boring Road, Patna", "Skin rash flare-up"),
            ("P019", "Ajay Saxena", 44, "Male", "9944556677", "ajay.saxena@example.com", "Swaroop Nagar, Kanpur", "Lower back spasm"),
            ("P020", "Sunita Mishra", 38, "Female", "9955667788", "sunita.mishra@example.com", "Assi Ghat Road, Varanasi", "Routine gynaecological review"),
            ("P021", "Rohan Bhatia", 30, "Male", "9966778899", "rohan.bhatia@example.com", "Model Town, Ludhiana", "Sports injury, right ankle"),
            ("P022", "Divya Menon", 35, "Female", "9977889900", "divya.menon@example.com", "Vellayambalam, Thiruvananthapuram", "Seasonal bronchitis"),
            ("P023", "Sanjay Kulkarni", 55, "Male", "9988990011", "sanjay.kulkarni@example.com", "College Road, Nashik", "Mild coronary artery disease"),
            ("P024", "Shilpa Singhania", 42, "Female", "9999001122", "shilpa.singhania@example.com", "Sanjay Place, Agra", "Iron deficiency anemia"),
            ("P025", "Manoj Tiwari", 49, "Male", "9700112233", "manoj.tiwari@example.com", "Civil Lines, Prayagraj", "High triglycerides"),
            ("P026", "Tanvi Agarwal", 26, "Female", "9711223344", "tanvi.agarwal@example.com", "Shastri Nagar, Meerut", "Food allergy reaction"),
            ("P027", "Harish Varma", 64, "Male", "9722334455", "harish.varma@example.com", "Kalawad Road, Rajkot", "Cataract pre-op clearance"),
            ("P028", "Rashmi Nambiar", 33, "Female", "9733445566", "rashmi.nambiar@example.com", "Mavoor Road, Kozhikode", "Mild insomnia & stress")
        ]
        cursor.executemany(
            """INSERT INTO patients (patient_code, full_name, age, gender, phone, email, address, medical_history)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            patients_data
        )

    # 4. Seed Appointments (15 appointments: 5 Pending, 5 Confirmed, 3 Completed, 2 Cancelled)
    appointments_count = cursor.execute("SELECT COUNT(*) as c FROM appointments").fetchone()['c']
    if appointments_count == 0:
        appointments_data = [
            ("A001", 1, 1, "2026-10-25", "10:00 AM", "Routine Cardiology Checkup & ECG", "Confirmed", "Patient requested morning slot."),
            ("A002", 2, 2, "2026-10-25", "11:30 AM", "Persistent high seasonal fever and chills", "Pending", "First visit for patient."),
            ("A003", 3, 3, "2026-10-24", "09:00 AM", "Child wellness checkup & vaccination review", "Completed", "Immunization updated."),
            ("A004", 4, 4, "2026-10-24", "11:00 AM", "Knee joint discomfort during climbing stairs", "Cancelled", "Patient rescheduled."),
            ("A005", 5, 5, "2026-10-26", "10:30 AM", "Consultation for maternal healthcare", "Pending", "Awaiting confirmation from lab."),
            ("A006", 6, 6, "2026-10-26", "02:00 PM", "Skin allergy consultation & patch test", "Confirmed", "Fast-track appointment."),
            ("A007", 7, 1, "2026-10-27", "09:30 AM", "Blood pressure follow-up consultation", "Pending", "Blood report requested."),
            ("A008", 8, 7, "2026-10-27", "10:15 AM", "Severe migraine evaluation & MRI review", "Confirmed", "Reports attached to file."),
            ("A009", 9, 2, "2026-10-28", "11:00 AM", "High fasting blood sugar consultation", "Pending", "HbA1c test required."),
            ("A010", 10, 4, "2026-10-28", "01:00 PM", "Arthritis joint therapy & mobility review", "Confirmed", "Physiotherapy follow-up."),
            ("A011", 11, 8, "2026-10-29", "03:00 PM", "Preventive oncology screening consultation", "Pending", "Family history documented."),
            ("A012", 12, 5, "2026-10-23", "04:00 PM", "Annual wellness health assessment", "Completed", "Vitals all normal."),
            ("A013", 13, 1, "2026-10-23", "11:30 AM", "Post-angioplasty annual review", "Completed", "Stent patent, ECHO normal."),
            ("A014", 14, 6, "2026-10-22", "03:30 PM", "Acne dermatological topical treatment", "Completed", "Prescription renewed."),
            ("A015", 15, 7, "2026-10-21", "10:00 AM", "Rescheduled neurological review", "Cancelled", "Cancelled by clinic.")
        ]
        cursor.executemany(
            """INSERT INTO appointments (appointment_code, patient_id, doctor_id, appointment_date, appointment_time, reason, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            appointments_data
        )

    # 5. Seed a demo initial backup record so backup screen has live status
    backups_count = cursor.execute("SELECT COUNT(*) as c FROM backups").fetchone()['c']
    if backups_count == 0:
        cursor.execute(
            """INSERT INTO backups (filename, file_size_kb, s3_bucket, s3_key, status, message, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "hospital_backup_initial.db",
                44.8,
                "hospital-backups-123",
                "backups/hospital_backup_initial.db",
                "Uploaded",
                "Successfully uploaded to S3 bucket: hospital-backups-123 (AES256 Encrypted)",
                "2026-10-22 14:25:32"
            )
        )

    conn.commit()
    conn.close()
    print("Database initialized and successfully seeded with fictional hospital data.")

if __name__ == "__main__":
    seed_database()
