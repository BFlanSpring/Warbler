"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                        from unittest import TestCase
from models import db, User, Message

class MessageViewTestCase(TestCase):
    """Test views for message-related routes."""

    def setUp(self):
        """Create test client and add sample data."""
        User.query.delete()
        Message.query.delete()
        self.client = app.test_client()

    def test_add_message_form(self):
        """Test rendering the add message form."""
        response = self.client.get("/messages/new")
        self.assertIn(b"Add my message!", response.data)

    def test_add_message(self):
        """Test adding a new message."""
        user = User.create(username="testuser", password="password", email="test@test.com")
        self.client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "password"
            }
        )
        response = self.client.post(
            "/messages/new",
            data={
                "text": "Hello, World!"
            },
            follow_redirects=True
        )
        self.assertIn(b"Hello, World!", response.data)

    def test_view_message(self):
        """Test viewing a message."""
        user = User.create(username="testuser", password="password", email="test@test.com")
        message = Message(text="Hello, World!", user_id=user.id)
        db.session.add(message)
        db.session.commit()
        response = self.client.get(f"/messages/{message.id}")
        self.assertIn(b"Hello, World!", response.data)

    def tearDown(self):
        """Clean up after each test."""
        db.session.rollback()
            password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
