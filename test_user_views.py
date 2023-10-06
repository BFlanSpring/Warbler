from unittest import TestCase
from models import db, User, Message

class UserViewTestCase(TestCase):
    """Test views for user-related routes."""

    def setUp(self):
        """Create test client and add sample data."""
        User.query.delete()
        Message.query.delete()
        self.client = app.test_client()

    def test_signup_form(self):
        """Test rendering the signup form."""
        response = self.client.get("/signup")
        self.assertIn(b"Sign Up", response.data)

    def test_signup(self):
        """Test user registration."""
        response = self.client.post(
            "/signup",
            data={
                "username": "testuser",
                "password": "password",
                "email": "test@test.com"
            },
            follow_redirects=True
        )
        self.assertIn(b"Hello, testuser!", response.data)

    def test_login_form(self):
        """Test rendering the login form."""
        response = self.client.get("/login")
        self.assertIn(b"Log In", response.data)

    def test_login(self):
        """Test user login."""
        User.create(username="testuser", password="password", email="test@test.com")
        response = self.client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "password"
            },
            follow_redirects=True
        )
        self.assertIn(b"Hello, testuser!", response.data)

    def test_logout(self):
        """Test user logout."""
        User.create(username="testuser", password="password", email="test@test.com")
        self.client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "password"
            }
        )
        response = self.client.get("/logout", follow_redirects=True)
        self.assertIn(b"You are not logged in", response.data)

    def tearDown(self):
        """Clean up after each test."""
        db.session.rollback()
