from sqlalchemy.sql import text
from flask import Flask
from flask import redirect, render_template, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import getenv

from app import app, db



@app.route("/delete_message/<int:message_id>", methods=["POST"])
def delete_message(message_id):
    message = db.session.execute(text("SELECT posted_by FROM messages WHERE id = :id"), {"id": message_id}).mappings().fetchone()
    if not message or not check_user_is_permitted(message["posted_by"]):
        flash("You do not have permission to delete this message.", "error")
        return redirect(request.referrer or url_for('index'))

    try:
        db.session.execute(text("DELETE FROM messages WHERE id = :id"), {"id": message_id})
        db.session.commit()
        flash("Message deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete message.", "error")
        print(f"Error deleting message {message_id}: {e}")

    return redirect(request.referrer or url_for('index'))


@app.route("/edit_message/<int:message_id>", methods=["POST"])
def edit_message(message_id):
    new_content = request.form.get("new_content", "").strip()
    if not new_content:
        flash("Message content cannot be empty.", "error")
        return redirect(request.referrer or url_for('index'))
    
    message = db.session.execute(text("SELECT posted_by FROM messages WHERE id = :id"), {"id": message_id}).mappings().fetchone()

    # Check if the user is the poster of the message
    if not message or not check_user_is_permitted(message["posted_by"]):
        flash("You do not have permission to edit this message.", "error")
        return redirect(request.referrer or url_for('index'))

    try:
        db.session.execute(text("UPDATE messages SET content = :content WHERE id = :id"), {"content": new_content, "id": message_id})
        db.session.commit()
        flash("Message edited successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to edit message.", "error")
        print(f"Error editing message {message_id}: {e}")

    return redirect(request.referrer or url_for('index'))


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
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to post message to thread {thread_id}: {e}\n")
        flash("Failed to post message.", "error")
        return redirect(url_for("thread_func", thread_id=thread_id))
    return redirect(url_for("thread_func", thread_id=thread_id))


def check_user_is_permitted(needed_id):
    # Check if user is admin and can do anything that requires permissions
    print(f"Checking if user {session.get('user_id')} is permitted to access {needed_id}")
    print(f"Is admin: {session.get('is_admin')}")
    if session.get("is_admin"):
        return True
    return session.get("user_id") is not None and session["user_id"] == needed_id