from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, BooleanField
from wtforms.validators import InputRequired, EqualTo, Length, Regexp

class LoginForm(FlaskForm):
    username = StringField("Usuário", validators=[InputRequired()])
    password = PasswordField("Senha", validators=[InputRequired()])
    submit = SubmitField("Login")

class DeleteForm(FlaskForm):
    username = StringField("Usuário", validators=[InputRequired()])
    password = PasswordField("Senha", validators=[InputRequired()])
    submit = SubmitField("Excluir")

class MemberForm(FlaskForm):
    name = StringField("Nome", validators=[InputRequired()])
    id_type = StringField("Tipo de Documento", validators=[InputRequired()], render_kw={"placeholder": "RG, RNE, Passporte"})
    id_number = StringField("Nº do Documento", validators=[InputRequired()])
    submit = SubmitField("Adicionar")

class GuestForm(FlaskForm):
    name = StringField("Nome", validators=[InputRequired()])
    guest_id = HiddenField("Guest-ID")
    id_type = StringField("Tipo de Documento", validators=[InputRequired()], render_kw={"placeholder": "RG, RNE, Passporte"})
    id_number = StringField("Nº do Documento", validators=[InputRequired()])
    tm_member = BooleanField("É membro de outro clube?")
    submit = SubmitField("Adicionar")

class MemberChangeForm(FlaskForm):
    delete = BooleanField("Excluir?")
    member_id = HiddenField("Member-ID")
    name = StringField("Nome", validators=[InputRequired()])
    id_type = StringField("Tipo de Documento", validators=[InputRequired()], render_kw={"placeholder": "RG, RNE, Passporte"})
    id_number = StringField("Nº do Documento", validators=[InputRequired()])
    submit = SubmitField("Alterar")