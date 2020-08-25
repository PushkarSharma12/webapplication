from flask import Flask,render_template, url_for, request, flash, session
from flask import redirect
from flask_sqlalchemy import *
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from wtforms_fields import *
from passlib.hash import pbkdf2_sha256
from flask_login import LoginManager,AnonymousUserMixin, login_user, current_user, logout_user, login_required
from flask_script import Manager
from flask import Flask, render_template
from flask_socketio import SocketIO,send,emit, join_room
from flask_migrate import Migrate,MigrateCommand
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from models import *
from datetime import datetime,date,timedelta
import json

import os
import time
from flask_login import UserMixin
import pusher

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seckey'
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://pfflhnsoygfrwm:dbfb95b73b9e7f02027b474fd3255ab63ad6fe3c483194637e53b6ae0be90322@ec2-52-202-66-191.compute-1.amazonaws.com:5432/d7km9rfhq4orfd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
socketio = SocketIO(app)

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    """ User Model """
    __tablename__ = 'users'
    __searchable__ = ['username']
    id = db.Column(db.Integer, primary_key =True,autoincrement=True)
    username = db.Column(db.String(25), nullable = False)
    email = db.Column(db.String(85), unique=True, nullable = False)
    passworrd = db.Column(db.String(500), nullable = False)
    posts = db.relationship('Diary', foreign_keys='Diary.user_id',
                                    backref='poster',lazy='dynamic')
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                              foreign_keys=[Follow.followed_id],
                              backref=db.backref('followed', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()
    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User {0}>'.format(self.name)

    def get_id(self):
        return self.id
    def get_username(self):

        return self.username

    
    @classmethod
    def is_following(self, user):
        if user.id is None:
            return False
        return Follow.query.filter_by(
            followed_id=user.id,follower_id = self.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None
    
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            return True

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            return True
   
    

class Diary(db.Model):
    """ Diary Model """
    __tablename__ = 'diary'
    tweet_id = db.Column(db.Integer, primary_key= True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content =  db.Column(db.String(999),  nullable = False)
    topic =  db.Column(db.String(999),  nullable = False)
    posted = db.Column(db.DateTime, nullable=False)
    

    def __repr__(self):
        return '<Id {0} - {1}>'.format(self.tweet_id, self.tweet)



    @classmethod
    def delta_time(cls, tweet_posted):
        now = datetime.datetime.now()
        td = now - tweet_posted
        days = td.days
        hours = td.seconds//3600
        minutes = (td.seconds//60)%60
        if days > 0:
            return tweet_posted.strftime("%d %B, %Y")
        elif hours > 0:
            return str(hours) + 'h'
        elif minutes > 0:
            return str(minutes) + 'm'
        else:
            return 'few seconds ago'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)
    
   



manager.add_command('db', MigrateCommand)

pusher_client = pusher.Pusher(
  app_id='1061006',
  key='e1cd392b0a20b184ff8f',
  secret='2a0ebe35fdc23c2ea38d',
  cluster='ap2',
  ssl=True
)


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
    
    return render_template("dashboard.html", diary_content = diary_content, username = username_curr,user_id = user_id)


@app.route('/logout', methods = ['GET'])
@login_required
def logout():
    logout_user()
    flash('Please Login before accessing this!', 'danger')
    return redirect("/")


@app.route('/submitDiary', methods = ['POST','GET'])
@login_required
def submitDiary():
    username =  current_user.id
    today = date.today()
    topic = request.form['topic']
    content = request.form['text']
    diary_sub = Diary(poster=current_user, content = content, topic = topic,posted = today )
    db.session.add(diary_sub)
    db.session.commit()

    return redirect("/dashboard")

@app.route("/topic/<username>/<id>", methods = ['GET','POST'])
@login_required
def topic(username,id):
    user = username
    diary_id = id
    username_curr =  current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id
    if username_curr == user:
        diary = Diary.query.filter_by(tweet_id = diary_id, user_id = user_id)
        diary_content = Diary.query.filter_by(user_id = user_id)

        return render_template("topic.html", diary = diary, username = username_curr,diary_content = diary_content,one =1)
    else :
        return redirect("/dashboard")
    
@app.route("/topic/<username>/all", methods = ['GET','POST'])
@login_required
def all(username):
    user = username
    username_curr =  current_user.id
    if current_user.username == user:
        diary_content = Diary.query.filter_by(user_id = username_curr)

        return render_template("topic.html", username = current_user.id,all = 0,diary_content=diary_content)
        
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
    user = username
    sender_id = User.query.filter_by(username = user).first().id
    form = MessageForm()
    username_curr = current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id
    user = User.query.all()
    diary = Diary.query.filter_by(user_id = user_id)
    recieved_msg = Message.query.filter_by(recipient_id = user_id,sender_id = sender_id )
    sent_msg = Message.query.filter_by(sender_id = user_id,recipient_id = sender_id )
    #pusher_client.trigger('my-channel', 'my-event', {'message': 'hello world'})
    return render_template("chat.html",user_id = user_id,diary = diary, username = username_curr,user = user,chat =1,msg=username,form = form,recieved = recieved_msg,sent = sent_msg, sender_id = sender_id)

@socketio.on('message')
def handleMessage(msg):
    print("Message" + msg)
    send(msg, broadcast=True)

@app.route('/chat/sendmessage/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first()
    form = MessageForm()
    
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        return redirect(f'../{recipient}')
        

    return render_template('send_message.html', title=('Send Message'),form = form,
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
  

@app.route('/add/<username>')
@login_required
def follow_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('dashboard'))
    if current_user.is_following(user):
        flash('You are already following %s.' % user.username)
        return redirect(url_for('dashboard', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following %s.' % user.username)
    return redirect(url_for('dashboard', username=username))



if __name__ == "__main__":
    app.run(debug = True)