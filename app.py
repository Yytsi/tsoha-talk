from sqlalchemy.sql import text
from flask import Flask
from flask import redirect, render_template, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)

print(app.secret_key)
print(app.config["SQLALCHEMY_DATABASE_URI"])

# TODO: samesite cookies?

# Remember to wrap SQL queries in text()!

@app.route("/")
def index():
    if not session.get("user_id"):
        return redirect("/login")
    
    user = db.session.execute(text("SELECT username FROM users WHERE id = :id"), {"id": session["user_id"]}).fetchone()
    if user is None:
        return redirect("/login")

    # Display all forums visible to this user
    # i.e. all forums that are public, or that the user has access to

    forums_raw = db.session.execute(text("SELECT * FROM forums")).mappings().all()
    forums = [dict(forum) for forum in forums_raw]

    # Populate forums with last_msg and sum of messages
    for forum in forums:
        last_msg = db.session.execute(text("""
            SELECT content FROM messages 
            WHERE thread_id = (
                SELECT id FROM threads 
                WHERE forum_id = :forum_id 
                ORDER BY id DESC 
                LIMIT 1
            ) 
            ORDER BY id DESC 
            LIMIT 1
        """), {"forum_id": forum["id"]}).fetchone()

        if last_msg:
            forum["last_msg"] = last_msg[0]
        else:
            forum["last_msg"] = "No messages yet"

        message_count = db.session.execute(text("""
            SELECT COUNT(*) FROM messages 
            WHERE thread_id IN (
                SELECT id FROM threads 
                WHERE forum_id = :forum_id
            )
        """), {"forum_id": forum["id"]}).fetchone()

        forum["message_count"] = message_count[0]

        print(f"Message count for forum {forum['name']}: {message_count[0]}")
        print(f"Last message for forum {forum['name']}: {forum['last_msg']}")
    
    
    return render_template("index.html", username=user[0], forums=(forums or []))

@app.route("/create_forum", methods=["POST"])
def create_forum():
    forum_name = request.form["forum_name"]
    if not forum_name or len(forum_name) > 40:
        flash("Forum name too long or empty.", "error")
        return redirect(url_for('index'))
    try:
        db.session.execute(text("INSERT INTO forums (name) VALUES (:name)"), {"name": forum_name})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to create forum {forum_name}: {e}\n")
        flash("Failed to create forum.", "error")
        return redirect(url_for('index'))
    return redirect("/")

@app.route("/create_thread", methods=["POST"])
def create_thread():
    forum_id = request.form["forum_id"]
    thread_title = request.form["thread_title"]
    first_message = request.form["first_message"]

    if not thread_title or len(thread_title) > 40:
        flash("Thread title too long, empty, or it might be taken.", "error")
        return redirect(f"/forum/{forum_id}")
    if not first_message:
        flash("First message cannot be empty.", "error")
        return redirect(f"/forum/{forum_id}")
    try:
        db.session.execute(text("INSERT INTO threads (title, forum_id, creator_id) VALUES (:title, :forum_id, :creator_id)"), {"title": thread_title, "forum_id": forum_id, "creator_id": session["user_id"]})
        db.session.execute(text("INSERT INTO messages (content, thread_id, posted_by) VALUES (:content, (SELECT id FROM threads WHERE title = :title), :posted_by)"), {"content": first_message, "title": thread_title, "posted_by": session["user_id"]})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to create thread {thread_title}: {e}\n")
        flash("Failed to create thread.", "error")
        return redirect(url_for('index'))
    return redirect(f"/forum/{forum_id}")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form["username"]
        user = db.session.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone()
        if user is None:
            flash("No such user found", "error")
            return redirect(url_for("login"))
        password = request.form["password"]
        password_hash = db.session.execute(text("SELECT password FROM users WHERE username = :username"), {"username": username}).fetchone()[0]
        if not check_password_hash(password_hash, password):
            flash("Incorrect password", "error")
            return redirect(url_for("login"))
        session["user_id"] = user[0]
        return redirect("/")

@app.route("/logout", methods=["POST"])
def logout():
    try:
        session.pop("user_id", None)
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to log out user: {e}\n")
        flash("Failed to log out", "error")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password or len(password) < 6 or len(password) > 40 or len(username) < 5 or len(username) > 20:
            flash("Invalid input: Check username and password requirements.", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        try:
            db.session.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"), {"username": username, "password": password_hash})
            db.session.commit()
        except Exception as e:
            flash("Registration failed. Username might be taken, or another error occurred. ", "error")
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Failed to register user {username}: {e}\n")
            return redirect(url_for("register"))
        
        return redirect("/login")

def check_user_is_permitted(creator_id):
    print(f"Checking if user {session.get('user_id')} is permitted to modify thread created by {creator_id}")
    return session.get("user_id") is not None and session["user_id"] == creator_id

@app.route("/forum/<int:forum_id>", methods=["GET"])
def forum_func(forum_id):
    forum = db.session.execute(text("SELECT * FROM forums WHERE id = :id"), {"id": forum_id}).fetchone()
    if forum is None:
        flash("Forum not found. Are you sure it exists?", "error")
        return redirect(url_for("index"))

    # Get all threads for forum
    threads = db.session.execute(text("SELECT * FROM threads WHERE forum_id = :forum_id"), {"forum_id": forum_id}).mappings().all()

    # Need to check for each thread whether this user can modify its title or delete it

    threads = [dict(thread) for thread in threads]
    for thread in threads:
        thread["has_modify_permissions"] = check_user_is_permitted(thread['creator_id'])

    return render_template("forum.html", forum_name=forum[1], forum_id=forum_id, threads=threads)


@app.route("/thread/<int:thread_id>", methods=["GET"])
def thread_func(thread_id):
    thread = db.session.execute(text("SELECT * FROM threads WHERE id = :id"), {"id": thread_id}).fetchone()
    if thread is None:
        flash("Thread not found. Are you sure it exists?", "error")
        return redirect(url_for("index"))
    
    raw_messages = db.session.execute(text("SELECT * FROM messages WHERE thread_id = :id"), {"id": thread_id}).mappings().all()
    messages_with_usernames = []

    for message in raw_messages:
        user = db.session.execute(text("SELECT username FROM users WHERE id = :id"), {"id": message["posted_by"]}).mappings().first()
        if user:
            messages_with_usernames.append({**message, "username": user["username"]})
        else:
            messages_with_usernames.append({**message, "username": "Unknown"})

    return render_template("thread.html", thread_id=thread_id, thread_title=thread[1], messages=messages_with_usernames)

@app.route("/post_message", methods=["POST"])
def post_message():
    thread_id = request.form["thread_id"]
    message = request.form["message"]
    if not message:
        flash("Message cannot be empty", "error")
        
        return redirect(url_for("thread_func", thread_id=thread_id))
    try:
        db.session.execute(text("INSERT INTO messages (content, thread_id, posted_by) VALUES (:content, :thread_id, :posted_by)"), {"content": message, "thread_id": thread_id, "posted_by": session["user_id"]})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to post message to thread {thread_id}: {e}\n")
        flash("Failed to post message.", "error")
        return redirect(f"/thread/{thread_id}")
    return redirect(f"/thread/{thread_id}")

@app.route("/edit_thread/<int:thread_id>", methods=["POST"])
def edit_thread(thread_id):
    onwer_of_thread = db.session.execute(text("SELECT creator_id FROM threads WHERE id = :id"), {"id": thread_id}).fetchone()[0]
    if not check_user_is_permitted(onwer_of_thread):
        flash("You are not permitted to edit this thread.", "error")
        return redirect(f"/thread/{thread_id}")

    new_title = request.form["new_title"]
    if not new_title or len(new_title) > 40:
        flash("Thread title is too long or empty.", "error")
        return redirect(f"/thread/{thread_id}")

    try:
        db.session.execute(text("UPDATE threads SET title = :title WHERE id = :id AND creator_id = :creator_id"), {"title": new_title, "id": thread_id, "creator_id": session["user_id"]})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to edit thread {thread_id}: {e}\n")
        flash("Failed to edit thread title.", "error")
        return redirect(f"/thread/{thread_id}")

    flash("Thread title updated successfully.", "success")
    return redirect(f"/thread/{thread_id}")


@app.route("/delete_thread/<int:thread_id>", methods=["POST"])
def delete_thread(thread_id):
    try:
        # Check if user has permission to delete this thread
        onwer_of_thread = db.session.execute(text("SELECT creator_id FROM threads WHERE id = :id"), {"id": thread_id}).fetchone()[0]
        if not check_user_is_permitted(onwer_of_thread):
            flash("You are not permitted to delete this thread.", "error")
            return redirect(url_for("index"))
        
        thread = db.session.execute(text("SELECT creator_id FROM threads WHERE id = :id"), {"id": thread_id}).mappings().fetchone()
        if not thread or thread['creator_id'] != session["user_id"]:
            flash("You do not have permission to delete this thread.", "error")
            return redirect(url_for("index"))
        
        # Delete messages first
        db.session.execute(text("DELETE FROM messages WHERE thread_id = :id"), {"id": thread_id})
        # Then delete the thread
        db.session.execute(text("DELETE FROM threads WHERE id = :id"), {"id": thread_id})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to delete thread {thread_id}: {e}\n")
        flash("Failed to delete thread.", "error")
        return redirect(f"/thread/{thread_id}")

    flash("Thread deleted successfully.", "success")
    return redirect(url_for("index"))
    # TODO: redirect back to the forum where the thread was deleted from