from sqlalchemy.sql import text
from flask import Flask
from flask import redirect, render_template, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import getenv

from app import app, db



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
    
    
    return render_template("index.html", username=user[0], forums=(forums or []), is_admin=session.get("is_admin") is True)

