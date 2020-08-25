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
from wtforms_fields import *
from passlib.hash import pbkdf2_sha256
from flask_login import LoginManager,AnonymousUserMixin, login_user, current_user, logout_user, login_required
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from models import *
import os
import time

from flask_login import UserMixin
app = Flask(__name__)
app.secret_key='os.environ.get()'
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://pfflhnsoygfrwm:dbfb95b73b9e7f02027b474fd3255ab63ad6fe3c483194637e53b6ae0be90322@ec2-52-202-66-191.compute-1.amazonaws.com:5432/d7km9rfhq4orfd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)


manager.add_command('db', MigrateCommand)

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

    if current_user.is_authenticated:
        return redirect("/dashboard")
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
    username_curr = current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id

    if not current_user.is_authenticated:
        flash('Please Login before accessing this!', 'danger')
        return redirect("/login")
    

    diary_content = Diary.query.filter_by(user_id = user_id)
    
    return render_template("dashboard.html", diary_content = diary_content, username = username_curr)


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

@app.route('/chat', methods = ['GET', 'POST'])
@login_required
def chat():
    username_curr = current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id

    
    user = User.query.all()
    diary = Diary.query.filter_by(user_id = user_id)
    
    return render_template("chat.html",diary = diary, username = username_curr,user = user)


@app.route('/chat/<username>', methods = ['GET', 'POST'])
@login_required
def send_msg(username):
    form = MessageForm()
    username_curr = current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id
    user = User.query.all()
    diary = Diary.query.filter_by(user_id = user_id)
    


    return render_template("chat.html",diary = diary, username = username_curr,user = user,chat =1,msg=username,form = form)


@app.route('/chat/sendmessage/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        #db.session.add(msg)
        db.session.commit()
        return redirect(url_for('chat', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),form = form,
                            recipient=recipient)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    username_curr =  current_user.username
    diary = Diary.query.filter_by(username = username_curr)    
    return render_template('search.html',form  = form, diary = diary,username = username_curr)
  

@app.route('/search/<user>', methods=['GET', 'POST'])
@login_required
def searchRes(user):
    
    form = SearchForm()
    username = user
    search = "%{0}%".format(username)
    result = User.query.filter(User.username.like(search)).all()
    username_curr =  current_user.username
    diary = Diary.query.filter_by(username = username_curr)
    return render_template('search.html',form  = form, result= result, diary = diary,username = username_curr)
  

@app.route('/add/<username>/<friend_id>')
@login_required
def follow_user(username,friend_id):
    whom_id = friend_id
    username_curr= current_user.username
 
    who_id = User.query.filter_by(username = username_curr).first().id
    whom = db.session.query(User).filter_by(id=whom_id).first().username
    if who_id != whom_id:
        new_follow = Follower(
            who_id = who_id,
            whom_id=whom_id)
        try:
            db.session.add(new_follow)
            db.session.commit()
            return redirect(url_for('chat'))
        except IntegrityError:
            flash('You are already following {}'.format(whom))
            return redirect(url_for('chat'))
    else:
        
        return redirect(url_for('chat'))
    

if __name__ == "__main__":
    app.run(debug = True)
    

    