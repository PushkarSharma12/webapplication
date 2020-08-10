from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin,db.Model):
    """ User Model """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key =True)
    username = db.Column(db.String(25), unique=True, nullable = False)
    email = db.Column(db.String(85), unique=True, nullable = False)
    passworrd = db.Column(db.String(85), nullable = False)
