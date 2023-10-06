import os
import pdb

from flask import Flask, render_template, request, flash, redirect, jsonify, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, MessageForm, EditUserForm
from models import db, connect_db, User, Message

CURR_USER_KEY = "curr_user"
app = Flask(__name__)


# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup."""

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
                header_image_url=form.header_image_url.data,
                location=form.location.data,
                bio=form.bio.data,

            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    if g.user:
        do_logout()
        flash("User logged out", "success")
    else:
        flash("You are not logged in", "danger")

    return redirect("/")

##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.."""

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""


    user = User.query.get_or_404(user_id)

    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")



@app.route('/users/profile/<int:user_id>', methods=["GET", "POST"])
def profile(user_id):
    """Edit user profile."""

    # Ensure the user is logged in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Retrieve the user based on user_id
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        # Get the form data and password from the request
        form = EditUserForm(request.form)
        password = request.form.get('password')

        # Check if the password is correct
        if not user.check_password(password):
            flash("Incorrect password. Please try again.", "danger")
            return redirect(url_for("profile", user_id=user.id))

        if form.validate():
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            user.header_image_url = form.header_image_url.data
            user.bio = form.bio.data

            db.session.commit()

            flash("Profile updated successfully!", "success")
            return redirect(url_for("users_show", user_id=user.id))
    
    # If it's a GET request or the form is not valid, render the edit template
    return render_template('edit.html', user=user, form=EditUserForm(obj=user))



@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.route('/like/<int:message_id>', methods=['POST'])
def like_message(message_id):
    if not g.user:
        return jsonify(message="You must be logged in to like a warble"), 401

    message = Message.query.get_or_404(message_id)

    if g.user == message.user:
        return jsonify(message="You can't like your own warbles"), 400

    if message in g.user.likes:
        g.user.likes.remove(message)
    else:
        g.user.likes.append(message)

    db.session.commit()
    return jsonify(likes=len(g.user.likes))


@app.route('/unlike/<int:message_id>', methods=['POST'])
def unlike_message(message_id):
    if not g.user:
        return jsonify(message="You must be logged in to unlike a warble"), 401

    message = Message.query.get_or_404(message_id)

    if message in g.user.likes:
        g.user.likes.remove(message)
        db.session.commit()

    return jsonify(likes=len(g.user.likes))


@app.route('/liked_warbles')
def show_liked_warbles():
    if not g.user:
        flash("You must be logged in to view liked warbles.", "danger")
        return redirect(url_for("home"))

    liked_messages = g.user.likes
    return render_template("liked_warbles.html", liked_messages=liked_messages)



##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage for logged-in users."""

    # Check if the user is logged in
    if g.user:
        # Get the IDs of the users the logged-in user is following
        following_ids = [user.id for user in g.user.following]

        # Include the logged-in user's ID
        following_ids.append(g.user.id)

        # Query for the last 100 messages from the users the logged-in user is following
        messages = (Message.query
                    .filter(Message.user_id.in_(following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    # If the user is not logged in, you can provide a different view or redirect them
    # to the login page, for example.
    return render_template('index.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
