from wtforms import *


class LoginForm(Form):
    email = TextField('Email', [validators.Email()])
    password = PasswordField('Password', [validators.Length(min=1)])
    submit = SubmitField("Log In")