import argparse
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash
from os import getenv
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)

def create_admin(username, password):
    """Creates an admin user in the database."""
    with app.app_context():
        password_hash = generate_password_hash(password)
        sql = "INSERT INTO users (username, password, is_admin) VALUES (:username, :password, TRUE)"
        db.session.execute(text(sql), {"username": username, "password": password_hash})
        db.session.commit()
        print(f"Admin '{username}' created successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("username", type=str, help="The username of the admin.")
    parser.add_argument("password", type=str, help="The password of the admin.")
    args = parser.parse_args()

    create_admin(args.username, args.password)
