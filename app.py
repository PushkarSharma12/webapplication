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
from flask_socketio import SocketIO,send,emit, join_room, leave_room
from flask_migrate import Migrate,MigrateCommand
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
import secrets
from datetime import datetime,date,timedelta
import json
from PIL import Image
import os
import time
from flask_login import UserMixin
import pusher
from hashlib import md5

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seckey'
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://twnjjlkgkosact:3431c9e35b7c1bba7fe4c0e630391f876cc51acba24890d601afbdcb075d1496@ec2-3-220-222-72.compute-1.amazonaws.com:5432/d85fp0v33bols9'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.debug = True
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
    image_file = db.Column(db.String(150), nullable=False, default='default.png')
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
    def __init__(self, username=None, email=None, passworrd=None, image_file=None):
        self.username = username
        self.email = email
        self.passworrd = passworrd
        self.image_file = image_file

    def __repr__(self):
        return '<User {0}>'.format(self.name)

    def get_id(self):
        return self.id
    def get_username(self):

        return self.username

    def is_following(self, user):
            return self.followed.filter(
            Follow.followed_id == user.id).count() > 0

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None
    
    def follow(self, user):
        if user != self:
            if not self.is_following(user):
                f = Follow(follower=self, followed=user)
                db.session.add(f)
                db.session.commit()
                return True
        else :
            return False

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()
            return True
    def followed_posts(self):
        return Diary.query.join(
            Follow, (Follow.followed_id == Diary.user_id)).filter(
                Follow.follower_id == self.id).order_by(
                    Diary.posted.desc())
    def followerPost(self):
        return Diary.query.join(
            Follow, (Follow.followed_id == Diary.user_id)).filter(
                Follow.follower_id == self.id).order_by(
                    Diary.posted.desc())
        #user_tweets = Diary.query.filter_by(user_id = self.id)
        #followed_users = Diary.query.filter_by(user_id = self.followed.id)
        #posts = followed_tweets.join(user_tweets)
        #return posts
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        avatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
        self.image_file = avatar
        db.session.commit()
        return True

class Diary(db.Model):
    """ Diary Model """
    __tablename__ = 'diary'
    tweet_id = db.Column(db.Integer, primary_key= True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content =  db.Column(db.String(999),  nullable = False)
    topic =  db.Column(db.String(999),  nullable = False)
    posted = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    

    def __repr__(self):
        return '<Id {0} - {1}>'.format(self.tweet_id, self.tweet)



    @classmethod
    def delta_time(cls, tweet_posted):
        now = datetime.now()
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
        size = 400
        digest = md5(Email.lower().encode('utf-8')).hexdigest()
        avatars = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
        print(avatars)
        user = User(username=username, email = Email, passworrd = hashed_pwd,image_file = avatars )
        db.session.add(user)
        db.session.commit()
        flash('Registered Succesfully. Please Login', 'success')
        
        user_object = User.query.filter_by(username=username).first()
        login_user(user_object)
        return redirect(url_for('dashboard'))
    return render_template('signup.html',form = form)


@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/dashboard', methods = ['POST','GET'])
def dashboard():
    #print (f"{User..id}")
    form = SubmitDiary()
    if form.validate_on_submit():
        topic = form.topic.data
        content = form.content.data
        diary_sub = Diary(poster=current_user, content = content, topic = topic )
        db.session.add(diary_sub)
        db.session.commit()
    username_curr = current_user.username
    tweets = User.followed_posts(current_user)
    user_id = User.query.filter_by(username = username_curr).first().id
    picture = current_user.image_file
    if not current_user.is_authenticated:
        flash('Please Login before accessing this!', 'danger')
        return redirect("/login")
    

    diary_content = Diary.query.filter_by(user_id = user_id)
    
    return render_template("dashboard.html", diary_content = diary_content,
     username = username_curr,
     user_id = user_id,image_file = picture,
     all_tweets=User.followerPost(current_user),form = form)


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
    current_user.image_file
    topic = request.form['topic']
    content = request.form['text']
    if len(topic)<=140 and len(content)<=140:
        diary_sub = Diary(poster=current_user, content = content, topic = topic )
        db.session.add(diary_sub)
        db.session.commit()

    return redirect("/dashboard")

@app.route("/topic/<username>/<id>", methods = ['GET','POST'])
@login_required
def topic(username,id):
    picture = url_for('static', filename='profile_pics/' + current_user.image_file)
    user = username
    diary_id = id
    username_curr =  current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id
    if username_curr == user:
        diary = Diary.query.filter_by(tweet_id = diary_id, user_id = user_id)
        diary_content = Diary.query.filter_by(user_id = user_id)

        return render_template("topic.html", diary = diary, username = username_curr,diary_content = diary_content,one =1,image_file = picture)
    else :
        return redirect("/dashboard")
    
@app.route("/topic/<username>/all", methods = ['GET','POST'])
@login_required
def all(username):
    user = username
    image_file = current_user.image_file
    username_curr =  current_user.id
    if current_user.username == user:
        diary_content = Diary.query.filter_by(user_id = username_curr)

        return render_template("topic.html", username = current_user.username,all = 0,diary_content=diary_content,image_file = picture)
        
    else :
        return redirect("/dashboard")

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    
    username =  current_user.username
    diary_content = Diary.query.filter_by(user_id = current_user.id)
    posts= Diary.query.filter_by(user_id = current_user.id).count()
    no_posts = 0
    diary_content = Diary.query.filter_by(user_id = current_user.id)
    sorted_diary = diary_content.order_by(Diary.posted.desc())
    following = Follow.query.filter_by(followed_id = current_user.id).count()
    image_file = current_user.image_file
    return render_template('account.html', title='Account',
                           image_file=image_file,  username = username,
                           no_posts=posts,diary_content=sorted_diary,
                           follower_amt = following,other = False)

@app.route('/account/<username>', methods=['GET', 'POST'])
@login_required
def accountUser(username):
    username =  username
    if current_user.username == username:
        other = False
    else:
        other = True
    user = User.query.filter_by(username=username).first()
    diary_content = Diary.query.filter_by(user_id = user.id)
    posts= Diary.query.filter_by(user_id = user.id).count()
    no_posts = 0
    diary_content = Diary.query.filter_by(user_id = user.id)
    users = User.query.filter_by().all() 
    sorted_diary = diary_content.order_by(Diary.posted.desc())
    following = Follow.query.filter_by(followed_id = user.id).count()
    image_file = current_user.image_file
    return render_template('account.html', title='Account',
                           image_file=image_file,  username = username,
                           no_posts=posts,diary_content=sorted_diary,
                           follower_amt = following,other = other,
                           user = user,User=User,current = current_user)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    username =  current_user.username
    posts= Diary.query.filter_by(user_id = current_user.id).count()
    no_posts = 0
    form = UpdateAccountForm()
    following = Follow.query.filter_by(followed_id = current_user.id).count()
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for(f'accountUser'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        
    image_file = current_user.image_file
    return render_template('edit.html', title='Account',
                           image_file=image_file, form=form, 
                           username = username,all = 0,
                           no_posts=posts,follower_amt = following)

@app.route('/follow/<username>/<int:user_id>/')
@login_required
def follow_user(username, user_id):
    whom_id = user_id
    user = current_user
    following = User.query.filter_by(id= user_id).first() 
    User.follow(user, following)
    return redirect('/dashboard')

@app.route('/Unfollow/<username>/<int:user_id>/')
@login_required
def unfollow_user(username, user_id):
    whom_id = user_id
    user = current_user
    following = User.query.filter_by(id= user_id).first() 

    User.unfollow(user, following)
    return redirect('/dashboard')

@app.route('/search')
@login_required
def search():
    username =  current_user.username
    form = SearchForm()
    users = User.query.filter_by().all() 
    image_file = current_user.image_file
    return render_template("search.html",users=users,
    image_file=image_file,form=form,
    username = username,current = current_user,
    User=User)

@app.route('/notifications')
@login_required
def notification():
    username =  current_user.username
    image_file = current_user.image_file
    return render_template("notification.html",
    image_file=image_file,
    username = username,current = current_user,
    User=User)


if __name__ == "__main__":
    app.run(debug=True)
    
    #manager.run()

