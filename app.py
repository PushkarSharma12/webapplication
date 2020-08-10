from flask import Flask,render_template, url_for, request
from flask import redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length 

app = Flask(__name__)
app.config['SECRET_KEY'] = "thisisgood"
Bootstrap(app)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min = 4, max = 20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min = 8 ,max = 80)])

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Length(min = 4, max = 20)])
    username = StringField('Username', validators=[InputRequired(), Length(min = 4, max = 20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min = 8 ,max = 80)])
   

@app.route('/')
def index():
    return render_template('index.html')
    

@app.route('/login')
def login():
    form = LoginForm()


    return render_template('login.html',form = form)


@app.route('/signup')
def signup():
    form = RegisterForm()
    return render_template('signup.html',form = form)


@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == "__main__":
    app.run()

