from wtforms import *
import re


class LoginForm(Form):
    email = TextField('Email', [validators.Email()])
    password = PasswordField('Password', [validators.Length(min=1)])
    submit = SubmitField("Log In")
    
class RegistrationCodeForm(Form):
    code = TextField('Enter code...')
    submit = SubmitField("Register")
    
class ProfRegistrationForm(Form):
    school = SelectField('Choose a school')
    first_name = TextField('What is your first name?', [validators.Length(min=1)])
    last_name = TextField('And last name?', [validators.Length(min=1)])
    email = TextField("What's your (.edu) email address?", [validators.Email()])
    password = PasswordField("Create a password", [validators.Length(min=4)])
    password1 = PasswordField("Repeat password", [validators.EqualTo('password', message="Passwords must match")])
    submit = SubmitField("Register")
    
class CreateSchoolForm(Form):
    school_name = TextField('School Name', [validators.Length(min=1)])
    tags = TextField('Tags (space separated)')
    submit = SubmitField("Create School")

def time_validate(form, field):
    data = field.data.strip()
    match = re.match("^(?:0[1-9])|(?:[1-2]:[0-4]):[0-5][0-9]$", data)
    if not match:
        raise ValidationError("Time must be formatted like HH:MM military time")
def date_validate(form, field):
    data = field.data.strip()
    match = re.match("")
    
class CreateClassForm(Form):
    name = TextField("What's the name of your course?", [validators.Required])
    section = TextField("What is the section number of your course?")
    code = TextField("And the course code?")
    alternate_codes = TextField("Does it have any cross-listed codes? If not, leave this blank.")
    start_date = DateField("When does the course's term begin?", [validators.Required], format="%Y-%m-%d")
    finish_date = DateField("And end?", [validators.Required], format="%Y-%m-%d")
    m = TextField("Monday Start", [time_validate])
    m_end = TextField("Monday End", [time_validate])
    t = TextField("Tuesday Start", [time_validate])
    t_end = TextField("Tuesday End", [time_validate])
    w = TextField("Wednesday Start", [time_validate])
    w_end = TextField("Wednesday End", [time_validate])
    r = TextField("Thursday Start", [time_validate])
    r_end = TextField("Thursday End", [time_validate])
    f = TextField("Friday Start", [time_validate])
    f_end = TextField("Friday End", [time_validate])
    s = TextField("Saturday", [time_validate])
    s_end = TextField("Saturday End", [time_validate])
    u = TextField("Sunday", [time_validate])
    u_end = TextField("Sunday End", [time_validate])
    auto_convo = BooleanField("Create a conversation around every class")
    day_offset = IntegerField("Day offset", [validators.NumberRange(min=0, max=100)])
    hour_offset = IntegerField("Hour offset", [validators.NumberRange(min=0, max=59)])
    submit = SubmitField("Create Class")
