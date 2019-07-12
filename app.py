# encoding: utf-8
# encoding: iso-8859-1
# encoding: win-1252

import os
import requests
import csv
from datetime import datetime
from flask import Flask, render_template, url_for, redirect, request, flash, session, send_file, make_response
from flask_session import Session
from helpers import login_required
from forms import LoginForm, MemberForm, MemberChangeForm, DeleteForm, GuestForm, GuestChangeForm
from werkzeug import generate_password_hash, check_password_hash
from werkzeug.datastructures import MultiDict
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from database import Member, Guest, User
import pdfkit

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = "development"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

URL = os.getenv("DATABASE_URL")

engine = create_engine(URL)
db = scoped_session(sessionmaker(bind=engine))

# Ensure responses aren't cached
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

@app.route('/convidados', methods=['get', 'post'])
@login_required
def guests():
    """Show full list of guests and add new guests to list"""
    form = GuestForm()
    guests = db.query(Guest).order_by(Guest.guest_id)
    
    if form.validate_on_submit():
        db.add(Guest(name=form.name.data, id_type=form.id_type.data, id_number=form.id_number.data, tm_member=form.tm_member.data))
        db.commit()
        flash("Convidado adicionado com sucesso", "success")
        return redirect(url_for("guests"))
    
    return render_template("convidados.html", form=form, guests=guests)

@app.route('/lista')
@login_required
def lista():
    """Show complete list with both club members and guests"""
    members = db.query(Member).order_by(Member.name)
    guests = db.query(Guest).order_by(Guest.name)

    return render_template("/lista.html", members=members, guests=guests)

@app.route('/alterarmembro', methods=['POST'])
@login_required
def alterar_membro():
    """Change club member information or delete club member"""
    member_id = request.form.get('member-id')
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if member:
        form = MemberChangeForm(formdata=MultiDict({'name': member.name, 'id_type': member.id_type, 'id_number': member.id_number, 'member_id': member_id}))
    else:
        form = MemberChangeForm()
    if form.validate_on_submit():
        member_id = form.member_id.data
        if form.delete.data == True:
            session["to_delete"] = member_id
            session['origin'] = "membro"
            return redirect(url_for("delete"))
        else:
            db.query(Member).filter(Member.member_id == member_id).update({"name":form.name.data, "id_type":form.id_type.data, "id_number":form.id_number.data})
            db.commit()
            flash("Membro alterado com sucesso", "success")
            return redirect(url_for("members"))

    return render_template("alterar-membro.html", member=member, form=form)

@app.route('/alterarconvidado', methods=['POST'])
@login_required
def alterar_convidado():
    """Change guest information or delete guest"""
    guest_id = request.form.get('guest-id')
    guest = db.query(Guest).filter(Guest.guest_id == guest_id).first()
    if guest:
        form = GuestChangeForm(formdata=MultiDict({'name': guest.name, 'id_type': guest.id_type, 'id_number': guest.id_number, 'guest_id': guest.guest_id, 'tm_member': guest.tm_member}))
    else:
        form = GuestChangeForm()
    if form.validate_on_submit():
        guest_id = form.guest_id.data
        if form.delete.data == True:
            session["to_delete"] = guest_id
            session['origin'] = "convidado"
            return redirect(url_for("delete"))
        else:
            db.query(Guest).filter(Guest.guest_id == guest_id).update({"name":form.name.data, "id_type":form.id_type.data, "id_number":form.id_number.data, 'tm_member': form.tm_member.data})
            db.commit()
            flash("Convidado alterado com sucesso", 'success')
            return redirect(url_for("guests"))
    
    return render_template("alterar-convidado.html", form=form, guest=guest)

@app.route("/excluir", methods=['POST', 'GET'])
@login_required
def delete():
    """Require username and password to delete guest or club member"""
    delete_id = session["to_delete"]
    form = DeleteForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = db.query(User).filter(User.username == username).first()
        if user:
            if session["user_id"] == user.user_id:
                if check_password_hash(user.password, password):
                    if session['origin'] == 'convidado':
                        session['origin'] = None
                        db.query(Guest).filter(Guest.guest_id == delete_id).delete()
                        db.commit()
                        session["to_delete"] = None
                        flash("Convidado excluído com sucesso", 'success')
                        return redirect(url_for('guests'))

                    else:
                        db.query(Member).filter(Member.member_id == delete_id).delete()
                        db.commit()
                        session["to_delete"] = None
                        session['origin'] = None
                        flash("Membro excluído com sucesso", 'success')
                        return redirect(url_for('members'))                       
                    
                else:
                    session["to_delete"] = None
                    flash("Senha inválida", 'danger')
                    if session['origin'] == 'convidado':
                        session['origin'] = None
                        return redirect(url_for('guests'))
                    session['origin'] = None
                    return redirect(url_for('members'))
            else:
                session["to_delete"] = None
                flash("Usuário inválido", 'danger')
                if session['origin'] == 'convidado':
                    session['origin'] = None
                    return redirect(url_for('guests'))
                session['origin'] = None
                return redirect(url_for('members')) 
        else:
            session["to_delete"] = None
            flash("Usuário inválido", 'danger')
            if session['origin'] == 'convidado':
                session['origin'] = None
                return redirect(url_for('guests'))
            session['origin'] = None
            return redirect(url_for('members'))    

    return render_template("delete.html", form=form, delete_id=delete_id) 

@app.route('/exportar', methods=['GET'])
@login_required
def export():
    """Export the full list of guests and club members as a CSV file with current date"""
    date = datetime.today().strftime('%d-%m-%y')
    members = db.query(Member).order_by(Member.name)
    guests = db.query(Guest).order_by(Guest.name)

    with open(f'lista_{date}.csv', mode="w", encoding='utf-8') as csv_file:
        file_writer = csv.writer(csv_file, delimiter=',', dialect="excel")

        file_writer.writerow(["Membros"])
        file_writer.writerow(["Nome", "Documento", "Nº"])
        for member in members:
            file_writer.writerow([member.name, member.id_type, member.id_number])
        file_writer.writerow(["Convidados"])
        file_writer.writerow(["Nome", "Documento", "Nº"])
        for guest in guests:
            file_writer.writerow([guest.name, guest.id_type, guest.id_number])
        
    return send_file(f"./lista_{date}.csv", mimetype='text/csv', attachment_filename=f'lista_{date}.csv', as_attachment=True)

@app.route('/download_<type>', methods=['GET'])
@login_required
def download(type):
    date = datetime.today().strftime('%d-%m-%y')
    members = db.query(Member).order_by(Member.name)
    guests = db.query(Guest).order_by(Guest.name)
    rendered_page = render_template("/lista_export.html", members=members, guests=guests)

    if type == "html":
        with open(f'lista_{date}.html', mode="w", encoding='utf-8') as html_file:
            html_file.write(rendered_page)
        return send_file(f"./lista_{date}.html", mimetype='text/html', attachment_filename=f'lista_{date}.html', as_attachment=True)
    
    if type == "pdf":
        path = r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        config = pdfkit.configuration(wkhtmltopdf=path)
        css = r".\static\styles.css"
        pdf = pdfkit.from_string(rendered_page, False, configuration=config, css=css)
        filename = f'lista_{date}.pdf'
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'

        return response

@app.route('/login', methods=['POST', 'GET'])
def login():
    """Allow users to login to the website"""
    # Checks if user is already logged and redirects to index
    if session.get("user_id"):
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_info = db.execute("SELECT * FROM users WHERE username = :username", {'username': username}).fetchall()
        if user_info:
            if check_password_hash(user_info[0][2], password):
                session["user_id"] = user_info[0][0]
                flash(f"Boas-vindas, {user_info[0][3]}", 'success')
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
    """Logs user out and ends the session"""
    session.clear()
    flash("Você encerrou a sessão", "success")
    return redirect("/")

@app.route("/membros", methods=['GET', 'POST'])
@login_required
def members():
    """Show full list of club members and add new club members to list and database"""
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