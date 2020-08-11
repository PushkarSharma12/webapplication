from flask import Flask,render_template, url_for, request, flash
from flask import redirect
from flask_sqlalchemy import *
from datetime import datetime
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from models import *
from wtforms_fields import *
from passlib.hash import pbkdf2_sha256
from flask_login import LoginManager, login_user, current_user, logout_user
import os
import time

app = Flask(__name__)
port = int(os.environ.get('PORT', 5000)) 
app.secret_key='os.environ.get()'
app.config['WTF_CSRF_SECRET_KEY'] = "b'f\xfa\x8b{X\x8b\x9eM\x83l\x19\xad\x84\x08\xaa"
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://pfflhnsoygfrwm:dbfb95b73b9e7f02027b474fd3255ab63ad6fe3c483194637e53b6ae0be90322@ec2-52-202-66-191.compute-1.amazonaws.com:5432/d7km9rfhq4orfd'
db = SQLAlchemy(app)
login = LoginManager(app)
login.init_app(app)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


Bootstrap(app)
class RegistrationForm(FlaskForm):
    """ Registration form"""

    username = StringField('Username', validators=[InputRequired(message="Username required"), Length(min=4, max=25, message="Username must be between 4 and 25 characters")])
    password = PasswordField('Password', validators=[InputRequired(message="Password required")])
    email = StringField('Email', validators=[InputRequired(message="Email Required"),Email('Email should be valid!')])

    def validate_username(self, username):
        user_object = User.query.filter_by(username=username.data).first()
        if user_object:
            raise ValidationError("Username already exists. Select a different username.")
    
    def validate_email(self, email):
        user_object = User.query.filter_by(username=email.data).first()
        if user_object:
            raise ValidationError("Email already exists.")

@app.route('/')
def index():
    return render_template('index.html')


@app.route("/login", methods=['GET', 'POST'])
def login():

    login_form = LoginForm()

    # Allow login if validation success
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(username=login_form.username.data).first()
        login_user(user_object)
        return redirect(url_for('dashboard'))
        

    return render_template("login.html", form=login_form)


@app.route('/signup', methods=['GET','POST'])
def signup():
    form = RegistrationForm()  

    if form.validate_on_submit():
        username = form.username.data
        Email = form.email.data
        password = form.password.data
        hashed_pwd = pbkdf2_sha256.hash(password)
        user = User(username=username, email = Email, passworrd = hashed_pwd )
        db.session.add(user)
        db.session.commit()

        return redirect("/success")

    return render_template('signup.html',form = form)


@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/dashboard', methods = ['POST','GET'])
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug = True)

