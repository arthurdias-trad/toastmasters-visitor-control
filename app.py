import os
import requests
from flask import Flask, render_template, url_for, redirect, request, flash, session
from flask_session import Session
from helpers import login_required
from forms import LoginForm
from werkzeug import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = "development"
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

URL = os.getenv("DATABASE_URL")

engine = create_engine(URL)
db = scoped_session(sessionmaker(bind=engine))

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
@login_required
def index():
    return render_template("/index.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_info = db.execute("SELECT * FROM users WHERE username = :username", {'username': username}).fetchall()
        if user_info:
            if check_password_hash(user_info[0][2], password):
                session["user_id"] = user_info[0][0]
                flash(f"Welcome, {username}", 'success')
                return redirect("/")
            else:
                flash("Invalid password", 'danger')
                return redirect(url_for('login'))
        else:
            flash("User not found", 'danger')
            return redirect(url_for('login'))

    return render_template('/login.html', form=form)

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out", "success")
    return redirect("/")

if __name__ == "__main__":
    app.run()