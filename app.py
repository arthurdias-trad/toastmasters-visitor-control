from flask import Flask, render_template, url_for
from helpers import login_required
from forms import LoginForm


app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = "development"


@app.route('/')
@login_required
def index():
    return render_template("/index.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    return render_template('/login.html', form=form)

if __name__ == "__main__":
    app.run()