from sqlalchemy.sql import text
from flask import Flask
from flask import redirect, render_template, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import getenv

from app import app, db




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
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to create thread {thread_title}: {e}\n")
        flash("Failed to create thread.", "error")
        return redirect(request.referrer or url_for('index'))
    return redirect(f"/forum/{forum_id}")



@app.route("/thread/<int:thread_id>", methods=["GET"])
def thread_func(thread_id):
    thread = db.session.execute(
        text("SELECT * FROM threads WHERE id = :id"), 
        {"id": thread_id}
    ).mappings().fetchone()

    if thread is None:
        flash("Thread not found. Are you sure it exists?", "error")
        return redirect(request.referrer or url_for('index'))

    raw_messages = db.session.execute(
        text("SELECT m.*, u.username FROM messages m JOIN users u ON m.posted_by = u.id WHERE m.thread_id = :id"),
        {"id": thread_id}
    ).mappings().all()

    search_query = request.args.get('query', '').strip()
    search_results = []
    if search_query:
        # Fetch only search results when there is a query
        search_results = db.session.execute(
            text("SELECT m.*, u.username FROM messages m JOIN users u ON m.posted_by = u.id WHERE m.thread_id = :thread_id AND m.content ILIKE :query"),
            {"thread_id": thread_id, "query": f"%{search_query}%"}
        ).mappings().all()

    return render_template("thread.html", thread_id=thread_id, thread_title=thread['title'], messages=raw_messages, search_results=search_results, search_query=search_query)

@app.route("/edit_thread/<int:thread_id>", methods=["POST"])
def edit_thread(thread_id):
    onwer_of_thread = db.session.execute(text("SELECT creator_id FROM threads WHERE id = :id"), {"id": thread_id}).fetchone()[0]
    if not check_user_is_permitted(onwer_of_thread):
        flash("You are not permitted to edit this thread.", "error")
        return redirect(request.referrer or url_for('index'))

    new_title = request.form["new_title"]
    if not new_title or len(new_title) > 40:
        flash("Thread title is too long or empty.", "error")
        return redirect(request.referrer or url_for('index'))

    try:
        db.session.execute(text("UPDATE threads SET title = :title WHERE id = :id AND creator_id = :creator_id"), {"title": new_title, "id": thread_id, "creator_id": session["user_id"]})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to edit thread {thread_id}: {e}\n")
        flash("Failed to edit thread title.", "error")
        return redirect(request.referrer or url_for('index'))

    flash("Thread title updated successfully.", "success")
    return redirect(request.referrer or url_for('index'))

@app.route("/delete_thread/<int:thread_id>", methods=["POST"])
def delete_thread(thread_id):
    try:
        # Check if user has permission to delete this thread
        onwer_of_thread = db.session.execute(text("SELECT creator_id FROM threads WHERE id = :id"), {"id": thread_id}).fetchone()[0]
        if not check_user_is_permitted(onwer_of_thread):
            flash("You are not permitted to delete this thread.", "error")
            return redirect(request.referrer or url_for('index'))
        
        thread = db.session.execute(text("SELECT creator_id FROM threads WHERE id = :id"), {"id": thread_id}).mappings().fetchone()
        if (not session.get("is_admin")) and (not thread or thread['creator_id'] != session["user_id"]):
            flash("You do not have permission to delete this thread.", "error")
            print(f"is admin: {session.get('is_admin')}")
            return redirect(request.referrer or url_for('index'))
        
        # Delete messages first
        db.session.execute(text("DELETE FROM messages WHERE thread_id = :id"), {"id": thread_id})
        # Then delete the thread
        db.session.execute(text("DELETE FROM threads WHERE id = :id"), {"id": thread_id})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Failed to delete thread {thread_id}: {e}\n")
        flash("Failed to delete thread.", "error")
        return redirect(request.referrer or url_for('index'))

    flash("Thread deleted successfully.", "success")
    return redirect(request.referrer or url_for('index'))


def check_user_is_permitted(needed_id):
    # Check if user is admin and can do anything that requires permissions
    print(f"Checking if user {session.get('user_id')} is permitted to access {needed_id}")
    print(f"Is admin: {session.get('is_admin')}")
    if session.get("is_admin"):
        return True
    return session.get("user_id") is not None and session["user_id"] == needed_id