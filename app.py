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

app.config.update(
    SESSION_COOKIE_HTTPONLY = True,
    SESSION_COOKIE_SECURE = False,      # Since this is a local HTTP server anyway, we don't need to set this to True
    SESSION_COOKIE_SAMESITE = 'Lax',
)

from routes.forums import *
from routes.threads import *
from routes.messages import *
from routes.users import *
from routes.general import *