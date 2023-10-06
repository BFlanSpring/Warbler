import os
from unittest import TestCase
from models import db, User

# Set the test database URL
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Import the app
from app import app

# Create tables for testing
db.create_all()

class UserModelTestCase(TestCase):
    """Test cases for the User model."""

    def setUp(self):
        """Create test client and add sample data."""
        User.query.delete()
        self.client = app.test_client()

    def test_user_create(self):
        """Test User.create method."""
        user = User.create(username="testuser", password="password", email="test@test.com")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("password"))

    def test_user_create_duplicate_username(self):
        """Test User.create with duplicate username."""
        user1 = User.create(username="testuser", password="password", email="test1@test.com")
        user2 = User.create(username="testuser", password="password", email="test2@test.com")
        self.assertIsNone(user2)  # User should not be created

    def test_user_create_invalid_email(self):
        """Test User.create with invalid email."""
        user = User.create(username="testuser", password="password", email="invalid-email")
        self.assertIsNone(user)  # User should not be created

    def test_user_authenticate(self):
        """Test User.authenticate method."""
        user = User.create(username="testuser", password="password", email="test@test.com")
        authenticated_user = User.authenticate(username="testuser", password="password")
        self.assertEqual(user, authenticated_user)

    def test_user_authenticate_invalid_username(self):
        """Test User.authenticate with invalid username."""
        User.create(username="testuser", password="password", email="test@test.com")
        authenticated_user = User.authenticate(username="invaliduser", password="password")
        self.assertIsNone(authenticated_user)  # Should return None

    def test_user_authenticate_invalid_password(self):
        """Test User.authenticate with invalid password."""
        User.create(username="testuser", password="password", email="test@test.com")
        authenticated_user = User.authenticate(username="testuser", password="wrongpassword")
        self.assertIsNone(authenticated_user)  # Should return None

    def test_user_repr(self):
        """Test User __repr__ method."""
        user = User.create(username="testuser", password="password", email="test@test.com")
        self.assertEqual(str(user), f"<User #{user.id}: {user.username}, {user.email}>")

    def test_user_following(self):
        """Test user following and is_following methods."""
        user1 = User.create(username="user1", password="password1", email="user1@test.com")
        user2 = User.create(username="user2", password="password2", email="user2@test.com")

        user1.following.append(user2)
        db.session.commit()

        self.assertTrue(user1.is_following(user2))
        self.assertFalse(user2.is_following(user1))

    def test_user_followed_by(self):
        """Test is_followed_by method."""
        user1 = User.create(username="user1", password="password1", email="user1@test.com")
        user2 = User.create(username="user2", password="password2", email="user2@test.com")

        user1.following.append(user2)
        db.session.commit()

        self.assertFalse(user1.is_followed_by(user2))
        self.assertTrue(user2.is_followed_by(user1))

    def tearDown(self):
        """Clean up after each test."""
        db.session.rollback()
