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
from flask import Flask, render_template,make_response,jsonify
from flask_socketio import SocketIO,send,emit, join_room, leave_room
from flask_migrate import Migrate,MigrateCommand
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
import secrets
from datetime import datetime,date,timedelta
from PIL import Image
import os
import time
from flask_login import UserMixin
from hashlib import md5
import json
from flask_json import FlaskJSON, JsonError, json_response
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'simple'})
app = Flask(__name__)
cache.init_app(app)
app.config['SECRET_KEY'] = 'seckey'
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://twnjjlkgkosact:3431c9e35b7c1bba7fe4c0e630391f876cc51acba24890d601afbdcb075d1496@ec2-3-220-222-72.compute-1.amazonaws.com:5432/d85fp0v33bols9'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.debug = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
json = FlaskJSON(app)
#manager = Manager(app)
socketio = SocketIO(app)

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    """ Like Model """
    __tablename__ = 'likes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('diary.tweet_id'),
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
    like = db.relationship('Like', foreign_keys='Like.user_id',
                                    backref='liker',lazy='dynamic')
    def __init__(self, username=None, email=None, passworrd=None, image_file=None):
        self.username = username
        self.email = email
        self.passworrd = passworrd
        self.image_file = image_file

    def __repr__(self):
        return '<User {0}>'.format(self.username)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

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
        followed = Diary.query.join(
             Follow, (Follow.followed_id == Diary.user_id)).filter(
                 Follow.follower_id == self.id)
        own = Diary.query.filter_by(user_id = self.id)
        return followed.union(own).order_by(Diary.posted.desc())
    def followerPost(self):
        # userPosts = Diary.query.filter_by(user_id = self.id).order_by(Diary.posted.desc())
        # followedPosts = Diary.query.join(
        #     Follow, (Follow.followed_id == Diary.user_id)).filter(
        #         Follow.follower_id == self.id).order_by(
        #             Diary.posted.desc())
        # return userPosts.join(Follow, (Follow.followed_id == Diary.user_id)).filter(
        #         Follow.follower_id == self.id).order_by(
        #             Diary.posted.desc()))
        return 1


    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        avatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
        self.image_file = avatar
        db.session.commit()
        return True

    def like_post(self, post):
        if not self.is_liking(post):
            f= Like(liker=self , liked_post=post)
            db.session.add(f)
            db.session.commit()
            return True

    def unlike(self, post):
        if self.is_liking(post):
            f = Like.query.filter_by(post_id=post.tweet_id,user_id=self.id).first()
            if f:
                db.session.delete(f)
                db.session.commit()
                return True

    def is_liking(self, post):
        return Like.query.filter(
            Like.user_id == self.id,
            Like.post_id == post.tweet_id).count() > 0

    def serialize(self,current_user):
        return {
           'id'         : self.id,
           'username'   : self.username,
           'email'   : self.email,
           'image_file' : self.image_file,
           'following'  : current_user.is_following(self),
           'isSame'     : current_user.id == self.id
       }
def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
class Diary(db.Model):
    """ Diary Model """
    __tablename__ = 'diary'
    tweet_id = db.Column(db.Integer, primary_key= True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content =  db.Column(db.String(999),  nullable = False)
    topic =  db.Column(db.String(999),  nullable = False)
    posted = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    liked_posts = db.relationship('Like',foreign_keys='Like.post_id',
                                    backref='liked_post',
                                    lazy='dynamic')
    def __repr__(self):
        return "<'Id {0} - {1} - {2}>'".format(self.tweet_id, self.content, self.topic)
    
    def serialize(self, user):
        """Return object data in easily serializable format"""
        return  {
                'id'         : self.tweet_id,
                'user_id'    : self.user_id,
                'topic'      : self.topic,
                'content'      : self.content,
                'posted': dump_datetime(self.posted),
                # This is an example how to deal with Many2Many relations
                'poster'   :{
                                'id'       :  {self.poster.id},
                                'username' :  {self.poster.username},
                                'email'    :  {self.poster.email},
                                'image_file': {self.poster.image_file}
                    },
                'liked'    : current_user.is_liking(self),
                'likes'    : Like.query.filter_by(post_id = self.tweet_id).count()
           }


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

#manager.add_command('db', MigrateCommand)



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

@app.route("/like", methods=['GET', 'POST'])

def like():
    return render_template("like.html")

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
def dashboard(page=1):
    #print (f"{User..id}")
    #post = Diary.query.filter_by(tweet_id = 1).first()
    #print(post.serialize(current_user))
    form = SubmitDiary()
    if form.validate_on_submit():
        topic = form.topic.data
        content = form.content.data
        diary_sub = Diary(poster=current_user, content = content, topic = topic )
        db.session.add(diary_sub)
        db.session.commit()
    username_curr = current_user.username
    tweets = current_user.followed_posts()
    user_id = User.query.filter_by(username = username_curr).first().id
    picture = current_user.image_file
    if not current_user.is_authenticated:
        flash('Please Login before accessing this!', 'danger')
        return redirect("/login")
    

    diary_content = Diary.query.filter_by(user_id = user_id)
    
    return render_template("dashboard.html", diary_content = diary_content,
     username = username_curr,
     current_user=current_user,user_id = user_id,image_file = picture,
     form = form,tweets=tweets)

@app.route("/load")
def load():
    """ Route to return the posts """

    time.sleep(0.1)  # Used to simulate delay
    tweets = current_user.followed_posts()
    if request.args:
        counter = int(request.args.get("c"))  # The 'counter' value sent in the QS
        print (counter)
        if counter == 0:
            print(f"Returning posts 0 to {5}")
            # Slice 0 -> quantity from the db
            res = make_response(jsonify([i.serialize(current_user) for i in tweets[0: 5]]), 200)
            print(res)
        elif counter == tweets.count():
            print("No more posts")
            res = make_response(jsonify({}))
            print(res)
        else:
            print(f"Returning posts {counter} to {counter + 5}")
            # Slice counter -> quantity from the db
            res = make_response(jsonify([i.serialize(current_user) for i in tweets[counter: counter+5]]), 200)
            print(res)
    return res

@app.route("/followLoad")
def followLoad():
    """ Route to return the posts """

    time.sleep(0.1)  # Used to simulate delay
    account = User.query.filter_by().all() 
    if request.args:
        counter = int(request.args.get("c"))  # The 'counter' value sent in the QS
        print (counter)
        if counter == 0:
            print(f"Returning posts 0 to {5}")
            # Slice 0 -> quantity from the db
            res = make_response(jsonify([i.serialize(current_user) for i in account[0: 10]]), 200)
            print(res)
        elif counter == account.count():
            print("No more posts")
            res = make_response(jsonify({}))
            print(res)
        else:
            print(f"Returning posts {counter} to {counter + 5}")
            # Slice counter -> quantity from the db
            res = make_response(jsonify([i.serialize(current_user) for i in tweets[counter: counter+25]]), 200)
            print(res)
    return res
# @app.route("/load/likes")
# def loadLikes():
#     """ Route to return the posts """

#     time.sleep(0.1)  # Used to simulate delay
#     tweets = current_user.followed_posts()
#     likes = [current_user.is_liking(i) for i in tweets]
#     if request.args:
#         counter = int(request.args.get("c"))  # The 'counter' value sent in the QS

#         if counter == 0:
#             print(f"Returning posts 0 to {5}")
#             # Slice 0 -> quantity from the db
#             res = make_response(jsonify([likes[0: 5]]), 200)
#             print(likes[0:5])
#         elif counter == tweets.count():
#             print("No more posts")
#             res = make_response(jsonify({}))
#             print()
#         else:
#             print(f"Returning posts {counter} to {counter + 5}")
#             # Slice counter -> quantity from the db
#             res = make_response(jsonify([likes[counter: counter+5]]), 200)
#             print(likes[counter: counter+5])
#     return res

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


@app.route('/like/<posted>/<typeLike>')
@login_required
def Like_Post(posted,typeLike):
    username =  current_user.id
    posts = posted
    typeLike = typeLike
    if typeLike == "like":
        post = Diary.query.filter_by(tweet_id=(posts)).first()
        like = User.like_post(current_user,post)

    elif typeLike == "unlike":
        post = Diary.query.filter_by(tweet_id=(posts)).first()
        like = User.unlike(current_user,post)
    else :
        res = make_response(jsonify({}), 200)
    return "done"

@app.route('/follow/<user_id>/<typeLike>')
@login_required
def Follow_User(user_id,typeLike):
    username =  current_user.id
    user = user_id
    typeLike = typeLike
    if typeLike == "follow":
        users = User.query.filter_by(id=(user)).first()
        current_user.follow(users)

    elif typeLike == "unfollow":
        users = User.query.filter_by(id=(user)).first()
        current_user.unfollow(users)
    else :
        res = make_response(jsonify({}), 200)
    return "done"
    

# @app.route("/topic/<username>/<id>", methods = ['GET','POST'])

# @app.route('/unlike/<diary_id>', methods = ['POST','GET'])

# @login_required
# def UnLikePost(diary_id):
#     username =  current_user.id
#     post = Diary.query.filter_by(tweet_id=diary_id).first()
#     like = User.unlike(current_user,post)
#     return redirect("/dashboard")

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
    sorted_diary = diary_content.order_by(Diary.posted.desc())
    following = Follow.query.filter_by(followed_id = user.id).count()
    image_file = current_user.image_file
    return render_template('account.html', title='Account',
                           image_file=image_file,  username = username,
                           no_posts=posts,diary_content=sorted_diary,
                           follower_amt = following,other = other,
                           user = user,User=User,current = current_user)


@app.route("/load/account/<username>")
def loadAccount(username):
    """ Route to return the posts """

    time.sleep(0.1)  # Used to simulate delay
    user = User.query.filter_by(username=username).first()
    tweets = Diary.query.order_by(Diary.posted.desc()).filter_by(user_id = user.id)
    if request.args:
        counter = int(request.args.get("c"))  # The 'counter' value sent in the QS

        if counter == 0:
            print(f"Returning posts 0 to {5}")
            # Slice 0 -> quantity from the db
            res = make_response(jsonify([i.serialize(current_user) for i in tweets[0: 5]]), 200)
            print(res)
        elif counter == tweets.count():
            print("No more posts")
            res = make_response(jsonify({}))
            print(res)
        else:
            print(f"Returning posts {counter} to {counter + 5}")
            # Slice counter -> quantity from the db
            res = make_response(jsonify([i.serialize(current_user) for i in tweets[counter: counter+5]]), 200)
            print(res)
    return res

    
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

