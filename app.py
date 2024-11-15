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
    
    return render_template("forum.html", forum_name=forum[1])