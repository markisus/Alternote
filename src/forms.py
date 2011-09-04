from wtforms import *

class RegistrationForm(Form):
    email = TextField('Email', [validators.Email()])
    university = SelectField('University', choices=[('Columbia', 'Columbia')])
    first_name = TextField('First Name', [validators.Length(min=1, max=35)])
    last_name = TextField('Last Name', [validators.Length(min=1, max=35)])
    password = PasswordField('Password', [validators.Length(min=1)])
    accept_rules = BooleanField('I accept the site rules', [validators.required()])
    submit = SubmitField('Register')
    
class ClassSearchForm(Form):
    tags = TextField('Search Terms', [validators.Length(min=1, max=80)])
    match = RadioField('Match', choices=[('all', 'all'), ('any','any')])
    submit = SubmitField('Find my class!')
    
class LoginForm(Form):
    email = TextField('Email', [validators.Email()])
    password = PasswordField('Password', [validators.Length(min=1)])
    submit = SubmitField("Log In")
    
class MakePostForm(Form):
    action = SelectField('action', choices = [('upvote_post', 'Upvote Post'), ('downvote_post', 'Downvote Post'), ('upvote_comment', 'Upvote Comment'), ('downvote_comment', 'Downvote Comment'), ('create_comment_for_post', 'Add Comment')]) #TODO: Pull these options into a separate module
    postid = HiddenField('postid')
    commentid = HiddenField('commentid')
    userid = HiddenField('userid')
    comment = TextField('comment')

class ChangePostForm(Form):
    action = SelectField('action', choices = [('upvote_post', 'Upvote Post'), ('downvote_post', 'Downvote Post')]) #TODO: Pull these options into a separate module
    postid = HiddenField('postid')
    userid = HiddenField('userid')
    
class MakeCommentForm(Form):
    action = SelectField('action', choices = [('create_comment_for_post', 'Add Comment')]) #TODO: Pull these options into a separate module
    postid = HiddenField('postid')
    commentid = HiddenField('commentid')
    userid = HiddenField('userid')
    comment = TextField('comment')
    submit = SubmitField('submit')
    
class ChangeCommentForm(Form):
    action = SelectField('action', choices = [('upvote_comment', 'Upvote Comment'), ('downvote_comment', 'Downvote Comment')]) #TODO: Pull these options into a separate module
    postid = HiddenField('postid')
    commentid = HiddenField('commentid')
    userid = HiddenField('userid')
    submit = SubmitField('submit')
    