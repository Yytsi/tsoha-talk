from sqlalchemy.sql import text
from flask import Flask
from flask import redirect, render_template, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import getenv

from app import app, db

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
        session["username"] = username
        # Check admin right for user
        session["is_admin"] = db.session.execute(text("SELECT is_admin FROM users WHERE id = :id"), {"id": user[0]}).fetchone()[0] == 1

        # Log the login
        db.session.execute(text("INSERT INTO login_log (user_id) VALUES (:user_id)"), {"user_id": user[0]})
        db.session.commit()
    
        return redirect("/")

@app.route("/logout", methods=["POST"])
def logout():
    try:
        session.pop("user_id", None)
    except Exception as e:
        db.session.rollback()
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
            db.session.rollback()
            flash("Registration failed. Username might be taken, or another error occurred. ", "error")
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Failed to register user {username}: {e}\n")
            return redirect(url_for("register"))
        
        return redirect("/login")