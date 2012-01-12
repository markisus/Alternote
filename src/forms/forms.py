from wtforms import *
import re
import os
import time

class LoginForm(Form):
    email = TextField('Email', [validators.Email()])
    password = PasswordField('Password', [validators.Length(min=1)])
    submit = SubmitField("Submit")
    
class MailingListForm(Form):
    email = TextField('Email address...', [validators.Email()])
    submit = SubmitField("Go")

class RegistrationCodeForm(Form):
    code = TextField('Access code...')
    submit = SubmitField("Go")
    
class ProfRegistrationForm(Form):
    school = SelectField('Where do you teach?')
    #instructor_type = SelectField('Are you a professor or TA?') Do we need this? TAs will sign up through registration codes
    first_name = TextField('What is your first name?', [validators.Length(min=1)])
    last_name = TextField('And last name?', [validators.Length(min=1)])
    email = TextField("Where do your students email you?", [validators.Email()])
    password = PasswordField("Create a password", [validators.Length(min=4)])
    password1 = PasswordField("Repeat password", [validators.EqualTo('password', message="Passwords must match")])
    image = FileField("It'd be nice to see your face around here. Mind uploading a photo?")
    submit = SubmitField("Register")

class RegistrationForm(Form):
    first_name = TextField('What is your first name?', [validators.Length(min=1)])
    last_name = TextField('And last name?', [validators.Length(min=1)])
    email = TextField("Where does your professor email you?", [validators.Email()])
    password = PasswordField("Create a password", [validators.Length(min=4)])
    password1 = PasswordField("Repeat password", [validators.EqualTo('password', message="Passwords must match")])
    image = FileField("It'd be nice (for us and the students) to see your face around here. Mind uploading a photo?")
    submit = SubmitField("Register")
    
class AdminRegistrationForm(Form):
    type = SelectField(choices=[("instructor", "Professor"), ("ta", "TA")])
    first_name = TextField('What is your first name?', [validators.Length(min=1)])
    last_name = TextField('And last name?', [validators.Length(min=1)])
    email = TextField("Email?", [validators.Email()])
    password = PasswordField("Create a password", [validators.Length(min=4)])
    password1 = PasswordField("Repeat password", [validators.EqualTo('password', message="Passwords must match")])
    image = FileField("It'd be nice (for us and the students) to see your face around here. Mind uploading a photo?")
    submit = SubmitField("Register")        
    
def validate_image(form, field):
    if field.data:
        field.data = re.sub(r'[^a-z0-9_.-]', '_', field.data)

def upload(request):
    UPLOAD_PATH = ""
    form = ProfRegistrationForm(request.POST)
    if form.image.data:
        image_data = request.FILES[form.image.name].read()
        open(os.path.join(UPLOAD_PATH, form.image.data), 'w').write(image_data)

class CreateSchoolForm(Form):
    school_name = TextField('School Name', [validators.Length(min=1)])
    tags = TextField('Tags (space separated)')
    submit = SubmitField("Create School")
    
class ChangePasswordForm(Form):
    old_pass = PasswordField("Old Password")
    new_pass = PasswordField("New Password", [validators.Length(min=4)])
    new_pass_repeat = PasswordField("Repeat New Password", [validators.EqualTo(fieldname="new_pass", message="Two new passwords do not match")])
    submit = SubmitField("Change Password")

def time_validate(form, field):
    if field.data:
        data = field.data.strip()
        try:
            valid = time.strptime(data, "%H:%M")
        except ValueError:
            raise ValidationError("Date must be formated YYYY-MM-DD")
    
def date_validate(form, field):
    if field.data:
        data = field.data.strip()
        try:
            valid = time.strptime(data, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Date must be formated YYYY-MM-DD")
        
class CreateClassForm(Form):
    name = TextField("What's the name of your course?", [validators.Required(), validators.Regexp(r"[\w|\-|%|:|,|\.|!]+")])
    section = TextField("What is the section number of your course?")
    code = TextField("And the course code?")
    alternate_codes = TextField("Does the course have any cross-listed codes? If not, leave this blank.")
    start_date = DateField("When does the course's term begin?", [validators.Required(message="YYYY-MM-DD")], format="%Y-%m-%d")
    finish_date = DateField("And end?", [validators.Required(message="YYYY-MM-DD")], format="%Y-%m-%d")
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
    auto_convo = BooleanField("Should we create a conversation around every class?")
    day_offset = IntegerField("Day offset", [validators.NumberRange(min=0, max=100)], default=0)
    hour_offset = IntegerField("Hour offset", [validators.NumberRange(min=0, max=59)], default=0)
    submit = SubmitField("Create Class")

class FileForm(Form):
    file = FileField("File Path")
    submit = SubmitField("Upload")

class CreateEventForm(Form):
    name = TextField("What's the name of this event?", [validators.Required()])
    submit = SubmitField("Save")
    begin_date = TextField("Start Date", [validators.Required()])
    begin_time = TextField("Start Time", [validators.Required()])
    end_date = TextField("End Date", [validators.Required()])
    end_time = TextField("End Time", [validators.Required()])
    hour_choices = [("%02d" % s, s) for s in range(1,13)]
    min_choices = [("%02d" % s, "%02d" % s) for s in range(0, 60)]
    am_pm = [("am", "am"), ("pm", "pm")]
    start_hour = SelectField("Start Hour", [validators.Required()], choices=hour_choices)
    start_minute = SelectField("Start Minute", [validators.Required()], choices=min_choices)
    start_am_pm = SelectField("start am/pm", [validators.Required()], choices=am_pm)
    end_hour = SelectField("End Hour", [validators.Required()], choices=hour_choices)
    end_minute = SelectField("End Minute", [validators.Required()], choices=min_choices)
    end_am_pm = SelectField("start am/pm", [validators.Required()], choices=am_pm)
    #all_day = BooleanField("All day")
    days_before = TextField("How long before should the conversation start?")
    day_offset = TextField("Day(s)")
    hour_offset = TextField("Hour(s)")
    attach_conversation = BooleanField("Auto-conversation for this event")
    event_type = SelectField("Type of event (optional)", choices=[('Other', 'Other'), ('Lecture', 'Lecture'), ('Homework', "Homework"), ("Assignment", "Assignment")])
    #files = FileField("Associated files")
