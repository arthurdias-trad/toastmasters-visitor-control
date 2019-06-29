# encoding: utf-8
# encoding: iso-8859-1
# encoding: win-1252

import os
import requests
from flask import Flask, render_template, url_for, redirect, request, flash, session
from flask_session import Session
from helpers import login_required
from forms import LoginForm, MemberForm, MemberChangeForm, DeleteForm
from werkzeug import generate_password_hash, check_password_hash
from werkzeug.datastructures import MultiDict
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from database import Member, Guest, User

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

@app.route('/alterarmembro', methods=['POST'])
def alterar_membro():
    member_id = request.form.get('member-id')
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if member:
        form = MemberChangeForm(formdata=MultiDict({'name': member.name, 'id_type': member.id_type, 'id_number': member.id_number, 'member_id': member_id}))
    else:
        form = MemberChangeForm()
    if form.validate_on_submit():
        member_id = form.member_id.data
        if form.delete.data == True:
            session["member_to_delete"] = member_id
            return redirect(url_for("delete"))
        else:
            db.query(Member).filter(Member.member_id == member_id).update({"name":form.name.data, "id_type":form.id_type.data, "id_number":form.id_number.data})
            db.commit()
            flash("Membro alterado com sucesso", "success")
            return redirect(url_for("members"))

    return render_template("alterar-membro.html", member=member, form=form)

@app.route("/excluirmembro", methods=['POST', 'GET'])
def delete():
    member_id = session["member_to_delete"]
    print(member_id)
    form = DeleteForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = db.query(User).filter(User.username == username).first()
        if user:
            if session["user_id"] == user.user_id:
                if check_password_hash(user.password, password):
                    db.query(Member).filter(Member.member_id == member_id).delete()
                    db.commit()
                    session["member_to_delete"] = None
                    flash("Membro excluído com sucesso", 'success')
                    return redirect(url_for('members'))
                else:
                    session["member_to_delete"] = None
                    flash("Senha inválida", 'danger')
                    return redirect(url_for('members'))
            else:
                session["member_to_delete"] = None
                flash("Usuário inválido", 'danger')
                return redirect(url_for('members')) 
        else:
            session["member_to_delete"] = None
            flash("Usuário inválido", 'danger')
            return redirect(url_for('members'))    

    return render_template("delete.html", form=form, member_id=member_id) 


@app.route('/login', methods=['POST', 'GET'])
def login():
    if session["user_id"]:
        return redirect(url_for('index'))
    
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_info = db.execute("SELECT * FROM users WHERE username = :username", {'username': username}).fetchall()
        if user_info:
            if check_password_hash(user_info[0][2], password):
                session["user_id"] = user_info[0][0]
                flash(f"Boas-vindas, {username}", 'success')
                return redirect("/")
            else:
                flash("Senha inválida", 'danger')
                return redirect(url_for('login'))
        else:
            flash("Usuário inválido", 'danger')
            return redirect(url_for('login'))

    return render_template('/login.html', form=form)

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    session.clear()
    flash("Você encerrou a sessão", "success")
    return redirect("/")

@app.route("/membros", methods=['GET', 'POST'])
def members():
    form = MemberForm()
    members = db.query(Member).order_by(Member.member_id)

    if form.validate_on_submit():
        db.add(Member(name=form.name.data, id_type=form.id_type.data, id_number=form.id_number.data))
        db.commit()
        flash("Membro adicionado com sucesso", "success")
        return redirect(url_for("members"))
    
    return render_template("membros.html", form=form, members=members)


if __name__ == "__main__":
    app.run()