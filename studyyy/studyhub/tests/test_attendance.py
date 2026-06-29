import unittest
from app import app, db, User
from werkzeug.security import generate_password_hash


class AttendanceModuleTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            WTF_CSRF_ENABLED=False,
            SECRET_KEY='test-secret'
        )
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
            user = User(
                username='Test Student',
                email='test@student.com',
                password=generate_password_hash('password123', method='pbkdf2:sha256')
            )
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def test_attendance_page_loads_and_records_entry(self):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.user_id)
            session['_fresh'] = True

        response = self.client.get('/attendance')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/attendance/add', data={
            'subject': 'Mathematics',
            'status': 'Present',
            'date': '2026-06-28',
            'notes': 'Attended lecture'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Attendance', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
