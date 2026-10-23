import os
import unittest
from app import app
import database
import s3_backup

class HospitalManagementTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_login_page_renders(self):
        """Test login page renders with HTTP 200."""
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Admin Login", res.data)
        self.assertIn(b"Better Care", res.data)

    def test_02_login_and_dashboard(self):
        """Test login with default admin credentials."""
        res = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dashboard", res.data)
        self.assertIn(b"Total Patients", res.data)
        self.assertIn(b"Total Doctors", res.data)

    def test_03_patients_list(self):
        """Test patients list page and search."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['full_name'] = 'Administrator'
            sess['role'] = 'Administrator'

        res = self.client.get('/patients')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Rahul Sharma", res.data)

        # Search query
        search_res = self.client.get('/patients?q=Sharma')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b"Rahul Sharma", search_res.data)

    def test_04_add_patient(self):
        """Test adding a new patient via form POST."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['full_name'] = 'Administrator'
            sess['role'] = 'Administrator'

        res = self.client.post('/patients/add', data={
            'full_name': 'Test College Patient',
            'age': '24',
            'gender': 'Male',
            'phone': '9988776655',
            'email': 'college.student@test.com',
            'address': 'Campus Hostel Block 4',
            'medical_history': 'None'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Test College Patient", res.data)

    def test_05_doctors_directory(self):
        """Test doctor directory renders all doctors."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['full_name'] = 'Administrator'
            sess['role'] = 'Administrator'

        res = self.client.get('/doctors')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dr. Priya Singh", res.data)
        self.assertIn(b"Cardiologist", res.data)

    def test_06_appointments_and_booking(self):
        """Test appointment booking and appointment list."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['full_name'] = 'Administrator'
            sess['role'] = 'Administrator'

        # Book page GET
        res_get = self.client.get('/appointments/book')
        self.assertEqual(res_get.status_code, 200)
        self.assertIn(b"Available Doctors", res_get.data)

        # Book appointment POST
        res_post = self.client.post('/appointments/book', data={
            'patient_id': '1',
            'doctor_id': '1',
            'appointment_date': '2026-11-01',
            'appointment_time': '10:00 AM',
            'reason': 'Automated Test Checkup'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn(b"Appointment successfully scheduled!", res_post.data)

    def test_07_backup_page_and_trigger(self):
        """Test S3 backup page and backup generation."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['full_name'] = 'Administrator'
            sess['role'] = 'Administrator'

        res_get = self.client.get('/backup')
        self.assertEqual(res_get.status_code, 200)
        self.assertIn(b"Database Backup", res_get.data)
        self.assertIn(b"hospital-backups-123", res_get.data)

        # Trigger backup POST
        res_post = self.client.post('/backup/create', follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn(b"Database backup", res_post.data)

    def test_08_settings_and_s3_test_ajax(self):
        """Test settings view and AJAX S3 test."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['full_name'] = 'Administrator'
            sess['role'] = 'Administrator'

        res_settings = self.client.get('/settings')
        self.assertEqual(res_settings.status_code, 200)
        self.assertIn(b"Profile", res_settings.data)

        # Test S3 connection API
        res_ajax = self.client.post('/settings/test-s3')
        self.assertEqual(res_ajax.status_code, 200)
        json_data = res_ajax.get_json()
        self.assertIn('status', json_data)

if __name__ == '__main__':
    unittest.main()
