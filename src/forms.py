from wtforms import *


class LoginForm(Form):
    email = TextField('Email', [validators.Email()])
    password = PasswordField('Password', [validators.Length(min=1)])
    submit = SubmitField("Log In")
    
class RegistrationCodeForm(Form):
    code = TextField('Code')
    submit = SubmitField("Register")
    
class ProfRegistrationForm(Form):
    school = SelectField('Choose a school:')
    first_name = TextField('What is your first name?', [validators.Length(min=1)])
    last_name = TextField('And last name?', [validators.Length(min=1)])
    email = TextField("What's your (.edu) email address?", [validators.Email()])
    password = PasswordField("Create a password")
    password1 = PasswordField("Repeat password", [validators.EqualTo('password', message="Passwords must match")])
    