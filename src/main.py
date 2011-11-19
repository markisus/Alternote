import os.path
import cgi
import tornado.ioloop
import tornado.web
from jinja2 import Environment, PackageLoader
from db.utils import *
import json
from forms import *
from conversation_api import *

#Global Vars
env = Environment(variable_start_string='[[', variable_end_string=']]', loader=PackageLoader('res', 'templates'))
prof_code = "alternote_rocks"

#The 'index' page: handles registration code redirects
class LandingPage(tornado.web.RequestHandler):
    template = env.get_template('landing_page.template')
    def get(self):
        #Display the landing page
        self.write(self.template.render(form=RegistrationCodeForm()))
        
    def post(self):
        #Handle the registration code
        code = self.get_argument("code")
        if (code == prof_code):
            self.set_secure_cookie("code", code, expires_days=1)
            self.redirect(self.reverse_url('ProfessorRegistration'))
        else:
            pass #Try student signup
            
#Handles professor registration
class ProfessorRegistration(tornado.web.RequestHandler):
    template = env.get_template('professor_registration.template')
    def get(self):
        #Check registration code:
        code = self.get_secure_cookie("code")
        if code == prof_code:
            #Get a list of schools:
            self.write(self.template.render(form=ProfRegistrationForm()))
        
#class ViewPostsHandler(BaseHandler):
#    template = env.get_template('view_posts.template')
#    
#    @tornado.web.authenticated
#    def get(self, eventid):
#        get_event(eventid)
#        self.write(self.template.render(eventid=eventid, userid=self.get_current_user(), event=get_event(eventid)))   
#        
#        
#class UserHandler(BaseHandler):
#    template = env.get_template('user.template')
#    
#    @tornado.web.authenticated
#    def get(self, userid=None):
#        if not userid:
#            userid = self.get_current_user()
#        user = get_user(userid)
#        self.write(self.template.render(user=user))
#
#
#class ClassHandler(BaseHandler):
#    template = env.get_template('class.template')
#    
#    #@tornado.web.authenticated
#    def get(self, classid):
#        aclass = get_class(classid)
#        self.write(self.template.render(Class=aclass))
#
#        
#class EventHandler(BaseHandler):
#    template = env.get_template('event.template')
#    
#    @tornado.web.authenticated
#    def get(self, classid):
#        events = get_events_for_class(classid)
#        self.write(self.template.render(events=events))
#        
#
#class LoginHandler(BaseHandler):
#    template = env.get_template('login.template')
#
#    def get(self):
#        form = LoginForm()
#        
#        userid = self.get_current_user()
#        if userid:
#            self.write("Note: You are already logged in as " + userid)
#            
#        self.write(self.template.render(form=form))
#
#    def post(self):
#        form = LoginForm(**self.get_params())
#        if form.validate():
#            try:
#                user = get_user(form.email.data)
#            except KeyError:
#                self.write("No username or wrong password")
#                return
#            if user['password'] == form.password.data:
#                session = db_login(user['_id'])
#                self.set_cookie('session', session)
#                self.redirect('/me/')
#                return
#            
#            else:
#                self.write("No username or wrong password")
#        self.write(self.template.render(form=form))
#    
#    def delete(self):
#        self.set_secure_cookie('userid', None)
#        
#class LogoutHandler(BaseHandler):
#    @tornado.web.authenticated
#    def get(self):
#        self.clear_cookie('userid')
#        self.redirect('/login/')
        
application = tornado.web.Application([
    (r"/", LandingPage),
    tornado.web.URLSpec(r"/registration/professor/?", ProfessorRegistration, name="ProfessorRegistration"),
#    (r"/", LoginHandler),
#    (r'/me/?', UserHandler),
#    (r'/users/(.*)/?', UserHandler),
#    (r'/classes/(.*)/?', ClassHandler),
#    (r'/events/(.*)/?', EventHandler),
#    (r'/login/?', LoginHandler),
#    (r'/logout/?', LogoutHandler),
#    (r'/viewposts/(.*)/?', ViewPostsHandler),

    #SERVER API METHODS
        #/poll/(eventid)/(lastitem)
        #/get/(eventid)
        
        #/comment/(postid)/(message)
        #/post/(eventid)/(message)
        
        #/vote/post/(postid)
        #/unvote/post/(postid)
        #/flag/post/(postid)
        #/unflag/post/(postid)
        
        #/vote/comment/(commentid)
        #/unvote/comment/(commentid)
        #/flag/comment/(commentid)
        #/unflag/comment/(commentid)
    (r'/poll/(\w+)/(-1|\d+)/(\w+)/?', PollHandler),
    (r'/poll/(\w+)/(-1|\d+)/?', Randomizer), #
    (r'/get/(\w+)/?', PostGetter),
    (r'/comment/(\w+)/(.+)/?', Comment),
    (r'/post/(\w+)/(.+)/?', Post),
    (r'/anon_comment/(\w+)/(.+)/?', Comment, {'anon':True}),
    (r'/anon_post/(\w+)/(.+)/?', Post, {'anon':True}),
    (r'/vote/(\w+)/?', VoteObject),
    (r'/unvote/(\w+)/?', UnvoteObject),
    (r'/flag/(\w+)/', FlagObject),
    (r'/unflag/(\w+)/?', UnflagObject),
], 
                                      
    cookie_secret="CHANGE THIS EVENTUALLY",
    login_url= "/login/",
    static_path= os.path.join(os.path.dirname(__file__), "res", "static")
)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()