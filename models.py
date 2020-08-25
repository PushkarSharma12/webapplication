from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from datetime import date
from sqlalchemy.ext.associationproxy import association_proxy
import sys

db = SQLAlchemy()




class Follower(db.Model):
    __tablename__ = 'follower'
    __table_args__ = (
        db.PrimaryKeyConstraint('who_id', 'whom_id'),
    )

    who_id = db.Column(db.Integer)
    whom_id = db.Column(db.Integer)


    def __init__(self, who_id, whom_id):
        self.who_id = who_id
        self.whom_id = whom_id

    def __repr__(self):
        return '<User {0} follows {1}>'.format(self.who_id, self.whom_id)

class User(UserMixin, db.Model):
    """ User Model """
    __tablename__ = 'users'
    __searchable__ = ['username']
    id = db.Column(db.Integer, primary_key =True,autoincrement=True)
    username = db.Column(db.String(25), nullable = False)
    email = db.Column(db.String(85), unique=True, nullable = False)
    passworrd = db.Column(db.String(500), nullable = False)
    posts = db.relationship('Diary', backref='poster')
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)


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
    def is_following(cls, who_id, whom_id):
        whom_ids = db.session.query(Follower.whom_id).filter_by(who_id=who_id).all()
        whom_ids = [i[0] for i in whom_ids]
        if whom_id in whom_ids:
            return True
        else:
            return False
   
    def __init__(self, username=None, email=None, passworrd=None):
        self.username = username
        self.email = email
        self.passworrd = passworrd


    def __repr__(self):
        return '<User {0}>'.format(self.name)


class Diary(db.Model):
    """ Diary Model """
    __tablename__ = 'diary'
    tweet_id = db.Column(db.Integer, primary_key= True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content =  db.Column(db.String(999),  nullable = False)
    topic =  db.Column(db.String(999),  nullable = False)
    posted = db.Column(db.DateTime, nullable=False)
    
    def __init__(self,topic, content, posted, user_id):
        self.topic = topic
        self.content = content
        self.posted = posted
        self.user_id = user_id

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
    @classmethod
    def delta_time(cls, message_sent):
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



    