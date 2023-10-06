from unittest import TestCase
from models import db, User, Message

class MessageModelTestCase(TestCase):
    """Test cases for the Message model."""

    def setUp(self):
        """Create test client and add sample data."""
        User.query.delete()
        Message.query.delete()
        self.client = app.test_client()

    def test_message_create(self):
        """Test Message creation."""
        user = User.create(username="testuser", password="password", email="test@test.com")
        message = Message(text="Hello, World!", user_id=user.id)
        db.session.add(message)
        db.session.commit()
        self.assertEqual(message.text, "Hello, World!")

    def test_message_create_no_user(self):
        """Test Message creation without a user."""
        message = Message(text="Hello, World!")
        db.session.add(message)
        with self.assertRaises(Exception):
            db.session.commit()

    def test_message_repr(self):
        """Test Message __repr__ method."""
        user = User.create(username="testuser", password="password", email="test@test.com")
        message = Message(text="Hello, World!", user_id=user.id)
        db.session.add(message)
        db.session.commit()
        self.assertEqual(str(message), f"<Message #{message.id}: {message.text}, {message.timestamp}>")

    def tearDown(self):
        """Clean up after each test."""
        db.session.rollback()
