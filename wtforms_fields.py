from flask_wtf import FlaskForm
from wtforms import TextAreaField,StringField, PasswordField, SubmitField
from wtforms.validators import  DataRequired,InputRequired, Length, EqualTo, ValidationError
from passlib.hash import pbkdf2_sha256
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from app import *
from models import User


class SearchForm(FlaskForm):
    search = StringField('Search', [DataRequired()])
    submit = SubmitField('Search',
            render_kw={'class': 'btn btn-success btn-block'})

def invalid_credentials(form, field):
    """ Username and password checker """

    password = field.data
    username = form.username.data

    # Check username is invalid
    user_data = User.query.filter_by(username=username).first()
    if user_data is None:
        raise ValidationError("Username or password is incorrect")

    # Check password in invalid
    elif not pbkdf2_sha256.verify(password, user_data.passworrd):
        raise ValidationError("Username or password is incorrect")



class SubmitDiary(FlaskForm):
    topic = StringField ('',validators=[DataRequired(), Length(min=0, max=140)],render_kw={'class': 'heading','placeholder':'Topic '})
    content = TextAreaField('',validators=[
        DataRequired(), Length(min=0, max=140)],render_kw={'class': 'today','placeholder':'Write Content here....'})
    submit = SubmitField('Submit',
            render_kw={'class': 'btn btn-success btn-block'})
class LoginForm(FlaskForm):
    """ Login form """

    username = StringField('Username', validators=[InputRequired(message="Username required")])
    password = PasswordField('Password', validators=[InputRequired(message="Password required"), invalid_credentials])

class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField('Submit')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    