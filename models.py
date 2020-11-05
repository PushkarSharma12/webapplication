from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from datetime import date
from sqlalchemy.ext.associationproxy import association_proxy
import sys


db = SQLAlchemy()
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
    like = db.relationship('Like', foreign_keys='Like.user_id',
                                    backref='liker',lazy='dynamic')
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

    def like(self, post):
        if not self.is_liking(post):
            f = Like(liker=self, liked_post=post)
            db.session.add(f)
            db.session.commit()
            return True

    def unlike(self, post):
        if self.is_liking(post):
            f = Like.filter_by(post_id=post.id,user_id=self.id).first()
            if f:
                db.session.delete(f)
                db.session.commit()
                return True

    def is_liking(self, post):
        return Like.query.filter(
            Like.user_id == self.id,
            Like.post_id == post.tweet_id).count() > 0

    def serialize(self):
        return {
           'id'         : self.id,
           'username'   : self.username,
           'email'   : self.email,
           'image_file' : self.image_file,
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
    liked_post = db.relationship('Like',
                               foreign_keys='Like.post_id',
                               backref='liked_post',
                               lazy='dynamic')

    def __repr__(self):
        return "<'Id {0} - {1} - {2}>'".format(self.tweet_id, self.content, self.topic)
    
    @property
    def serialize(self):
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
                    }
            }
    
    def serialize_many2many(self):
       """
       Return object's relations in easily serializable format.
       NB! Calls many2many's serialize property.
       """
       return [ item.serialize for item in self.poster]

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