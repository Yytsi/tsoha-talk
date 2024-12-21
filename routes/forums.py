from sqlalchemy.sql import text
from flask import Flask
from flask import redirect, render_template, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import getenv

from app import app, db

@app.route("/create_secret_forum", methods=["POST"])
def create_secret_forum():
    forum_name = request.form["forum_name"]
    if not forum_name or len(forum_name) > 40:
        flash("Forum name too long or empty.", "error")
        return redirect(url_for('index'))
    
    try:
        db.session.execute(text("""
            INSERT INTO forums (name, is_secret, access_list)
            VALUES (:name, TRUE, '{}')
        """), {"name": forum_name})
        db.session.commit()
        flash("Secret forum created successfully.", "success")
    except Exception as e:
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to create secret forum {forum_name}: {e}\n")
        flash("Failed to create secret forum.", "error")
        return redirect(url_for('index'))
    
    return redirect(url_for('index')) 

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
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to create forum {forum_name}: {e}\n")
        flash("Failed to create forum.", "error")
        return redirect(url_for('index'))
    return redirect("/")


@app.route("/secret_forum_add_member", methods=["POST"])
def secret_forum_add_member():
    forum_id = request.form["forum_id"]
    username = request.form["username"]
    user_id = db.session.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone()
    if user_id is None:
        flash("No such user found", "error")
        return redirect(request.referrer or url_for('index'))

    try:
        forum = db.session.execute(text("SELECT is_secret FROM forums WHERE id = :id"), {"id": forum_id}).fetchone()
        if forum is None:
            flash("No such forum found", "error")
            return redirect(request.referrer or url_for('index'))
        
        if not forum[0]:  # Check if the forum is marked as secret
            flash("This forum is not a secret forum", "error")
            return redirect(request.referrer or url_for('index'))
        
        # Update the access list with the new user ID
        db.session.execute(text("""
            UPDATE forums
            SET access_list = array_append(access_list, :user_id)
            WHERE id = :forum_id
        """), {"user_id": str(user_id), "forum_id": forum_id})
        
        db.session.commit()
        flash("User added successfully to the forum", "success")
    except Exception as e:
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to add user {username} to forum {forum_id}: {e}\n")
        flash("Failed to add user to forum.", "error")
        return redirect(request.referrer or url_for('index'))

    return redirect(f"/forum/{forum_id}")


@app.route("/forum/<int:forum_id>", methods=["GET"])
def forum_func(forum_id):
    forum = db.session.execute(text("SELECT * FROM forums WHERE id = :id"), {"id": forum_id}).fetchone()
    if forum is None:
        flash("Forum not found. Are you sure it exists?", "error")
        return redirect(request.referrer or url_for('index'))
    
    # Check whether this forum is secret and user has access to it
    is_admin = session.get("is_admin") is True
    if (not is_admin) and (forum[2] and session.get("user_id") not in forum[3]):
        flash("You do not have access to this forum.", "error")
        return redirect(url_for('index'))

    # Get all threads for forum
    threads = db.session.execute(text("SELECT * FROM threads WHERE forum_id = :forum_id"), {"forum_id": forum_id}).mappings().all()

    # Need to check for each thread whether this user can modify its title or delete it

    threads = [dict(thread) for thread in threads]
    for thread in threads:
        thread["has_modify_permissions"] = check_user_is_permitted(thread['creator_id'])

    return render_template("forum.html", forum_name=forum[1], forum_id=forum_id, threads=threads, username=session.get("username"), is_admin=session.get("is_admin") is True)

@app.route("/delete_forum/<int:forum_id>", methods=["POST"])
def delete_forum(forum_id):
    try:
        # Check if user has permission to delete this forum
        if not session.get("is_admin"):
            flash("You are not permitted to delete this forum.", "error")
            return redirect(request.referrer or url_for('index'))
        
        db.session.execute(text("DELETE FROM forums WHERE id = :id"), {"id": forum_id})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to delete forum {forum_id}: {e}\n")
        flash("Failed to delete forum.", "error")
        return redirect(request.referrer or url_for('index'))

    flash("Forum deleted successfully.", "success")
    return redirect(request.referrer or url_for('index'))

def check_user_is_permitted(needed_id):
    # Check if user is admin and can do anything that requires permissions
    print(f"Checking if user {session.get('user_id')} is permitted to access {needed_id}")
    print(f"Is admin: {session.get('is_admin')}")
    if session.get("is_admin"):
        return True
    return session.get("user_id") is not None and session["user_id"] == needed_id