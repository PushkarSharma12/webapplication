from flask import Flask,render_template, url_for, request, flash, session
from flask import redirect
from flask_sqlalchemy import *
from datetime import datetime
from datetime import date
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from models import *
from wtforms_fields import *
from passlib.hash import pbkdf2_sha256
from flask_login import LoginManager,AnonymousUserMixin, login_user, current_user, logout_user, login_required
import os
import time

app = Flask(__name__)
app.secret_key='os.environ.get()'
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
        user_object = User.query.filter_by(email=email.data).first()
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
        flash('Registered Succesfully. Please Login', 'success')
        return redirect("/success")

    return render_template('signup.html',form = form)


@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/dashboard', methods = ['POST','GET'])
def dashboard():
    username = current_user.username
    if not current_user.is_authenticated:
        flash('Please Login before accessing this!', 'danger')
        return redirect("/login")
    

    diary_content = Diary.query.filter_by(username = username)
    
    return render_template("dashboard.html", diary_content = diary_content, username = username)


@app.route('/logout', methods = ['GET'])
@login_required
def logout():
    logout_user()
    flash('Please Login before accessing this!', 'danger')
    return redirect("/")


@app.route('/submitDiary', methods = ['POST','GET'])
@login_required
def submitDiary():
    username =  current_user.username
    today = date.today()
    topic = request.form['topic']
    content = request.form['text']
    users = Diary.query.filter_by(username = username).first()
    users2 = Diary.query.filter_by(username = username)
    if not users:
        id_per_user_new = 1
    else:
        for row in users2:
            id_per_user = row.id_per_user
            id_per_user_new = id_per_user+1
    diary_sub = Diary(username=username, id_per_user = id_per_user_new, content = content, topic = topic )
    db.session.add(diary_sub)
    db.session.commit()

    return redirect("/dashboard")

@app.route("/topic/<username>/<id>", methods = ['GET','POST'])
@login_required
def topic(username,id):
    diary_id = id
    username_curr =  current_user.username
    if username_curr == username:
        diary = Diary.query.filter_by(id_per_user = diary_id, username = username_curr)
        return render_template("topic.html", diary = diary, username = username_curr)
    else :
        return redirect("/dashboard")
    
@app.route("/topic/<username>/all", methods = ['GET','POST'])
@login_required
def all(username):
    username_curr =  current_user.username
    if username_curr == username:
        diary = Diary.query.filter_by(username = username_curr)
        return render_template("topic.html", diary = diary, username = username_curr)
    else :
        return redirect("/dashboard")

if __name__ == "__main__":
    app.run(debug = True)