from sqlalchemy.sql import text
from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)

print(app.secret_key)
print(app.config["SQLALCHEMY_DATABASE_URI"])

# remember to wrap SQL queries in text()!

@app.route("/")
def index():
    if not session.get("user_id"):
        return redirect("/login")
    
    user = db.session.execute(text("SELECT username FROM users WHERE id = :id"), {"id": session["user_id"]}).fetchone()
    if user is None:
        return redirect("/login")

    # display all forums visible to this user
    # i.e. all forums that are public, or that the user has access to

    forums = db.session.execute(text("SELECT * FROM forums")).fetchall()
    
    return render_template("index.html", username=user[0], forums=(forums or []))

@app.route("/create_forum", methods=["POST"])
def create_forum():
    forum_name = request.form["forum_name"]
    if not forum_name or len(forum_name) > 40:
        return render_template("error.html", message="Forum name too long or empty.")
    try:
        db.session.execute(text("INSERT INTO forums (name) VALUES (:name)"), {"name": forum_name})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to create forum {forum_name}: {e}\n")
        return render_template("error.html", message="Failed to create forum.")
    return redirect("/")

@app.route("/create_thread", methods=["POST"])
def create_thread():
    forum_id = request.form["forum_id"]
    thread_title = request.form["thread_title"]
    first_message = request.form["first_message"]

    if not thread_title or len(thread_title) > 40 or not first_message:
        return render_template("error.html", message="Thread title too long or empty, or it might be taken.")
    try:
        db.session.execute(text("INSERT INTO threads (title, forum_id, creator_id) VALUES (:title, :forum_id, :creator_id)"), {"title": thread_title, "forum_id": forum_id, "creator_id": session["user_id"]})
        db.session.execute(text("INSERT INTO messages (content, thread_id, posted_by) VALUES (:content, (SELECT id FROM threads WHERE title = :title), :posted_by)"), {"content": first_message, "title": thread_title, "posted_by": session["user_id"]})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to create thread {thread_title}: {e}\n")
        return render_template("error.html", message="Failed to create thread.")
    return redirect(f"/forum/{forum_id}")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form["username"]
        user = db.session.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone()
        if user is None:
            return render_template("error.html", message="No such user found")
        password = request.form["password"]
        password_hash = db.session.execute(text("SELECT password FROM users WHERE username = :username"), {"username": username}).fetchone()[0]
        if not check_password_hash(password_hash, password):
            return render_template("error.html", message="Incorrect password")
        session["user_id"] = user[0]
        return redirect("/")

@app.route("/logout", methods=["POST"])
def logout():
    try:
        session.pop("user_id", None)
    except:
        return render_template("error.html", message="Failed to log out")
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password or len(password) < 6 or len(password) > 40 or len(username) < 5 or len(username) > 20:
            return render_template("error.html", message="Invalid input: Check username and password requirements.")

        password_hash = generate_password_hash(password)
        try:
            db.session.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"), {"username": username, "password": password_hash})
            db.session.commit()
        except Exception as e:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Failed to register {username}: {e}\n")
            return render_template("error.html", message="Registration failed. Username might be taken, or another error occurred.")

        return redirect("/login")

@app.route("/forum/<int:forum_id>", methods=["GET"])
def forum(forum_id):
    forum = db.session.execute(text("SELECT * FROM forums WHERE id = :id"), {"id": forum_id}).fetchone()
    if forum is None:
        return render_template("error.html", message="Forum not found. Are you sure it exists?")
    
    # get all threads for forum
    threads = db.session.execute(text("SELECT * FROM threads WHERE forum_id = :forum_id"), {"forum_id": forum_id}).fetchall()
    print(threads)
    return render_template("forum.html", forum_name=forum[1], forum_id=forum_id, threads=threads)


@app.route("/thread/<int:thread_id>", methods=["GET"])
def thread(thread_id):
    thread = db.session.execute(text("SELECT * FROM threads WHERE id = :id"), {"id": thread_id}).fetchone()
    if thread is None:
        return render_template("error.html", message="Thread not found. Are you sure it exists?")
    
    # get all messages for thread, but also get the username of the poster, because id is not very informative
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
        return render_template("error.html", message="Message cannot be empty.")
    try:
        db.session.execute(text("INSERT INTO messages (content, thread_id, posted_by) VALUES (:content, :thread_id, :posted_by)"), {"content": message, "thread_id": thread_id, "posted_by": session["user_id"]})
        db.session.commit()
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to post message to thread {thread_id}: {e}\n")
        return render_template("error.html", message="Failed to post message.")
    return redirect(f"/thread/{thread_id}")