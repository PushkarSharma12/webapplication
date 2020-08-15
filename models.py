from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from datetime import date


db = SQLAlchemy()

class User(UserMixin, db.Model):
    """ User Model """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key =True,autoincrement=True)
    username = db.Column(db.String(25), nullable = False)
    email = db.Column(db.String(85), unique=True, nullable = False)
    passworrd = db.Column(db.String(85), nullable = False)

def get_username(self):
    return self.username
class Diary(db.Model):
    """ Diary Model """
    __tablename__ = 'diary'
    id = db.Column(db.Integer, primary_key= True)
    id_per_user = db.Column(db.Integer, nullable = False)
    username =db.Column(db.String(25),  nullable = False)
    content =  db.Column(db.String(999),  nullable = False)
    topic =  db.Column(db.String(999),  nullable = False)
    date =  db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

