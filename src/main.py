from forms import *
from forms.forms import RegistrationCodeForm, ProfRegistrationForm
from handlers import admin, registration, classes, misc, auth, calendar
from jinja2 import Environment, PackageLoader
from tornado.web import URLSpec
import cgi
import json
import os.path
import tornado.ioloop
import tornado.web
import handlers.env

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
    URLSpec(r"/", misc.LandingPage, name="LandingPage"),
    URLSpec(r"/registration/professor", registration.ProfessorRegistration, name="ProfessorRegistration"),
    
    #Auth
    URLSpec(r"/auth/login", auth.LoginHandler, name="LoginHandler"),
    
    #Admin Methods
    URLSpec(r"/admin/school/create", admin.CreateSchool, name="CreateSchool"),
    
    #Calendar
    URLSpec(r"/calendar/view/([\w|\-|%]+)", calendar.ViewCalendar, name="ViewCalendar"),
    URLSpec(r"/calendar/feed/([\w|\-|%]+)", calendar.CalendarFeed, name="CalendarFeed"),
    URLSpec(r"/calendar/details/(\w+)", calendar.CalendarDetails, name="CalendarDetails"),
    
    #Classes
    URLSpec(r"/classes/create", classes.CreateClass, name="CreateClass"),
    URLSpec(r"/classes/view", classes.ViewClasses, name="ViewClasses"),
    URLSpec(r"/classes/codes/([\w|\-|%]+)", classes.ViewCodes, name="ViewCodes"),

	#Pages
	URLSpec(r"/pages/about", misc.About, name="About"),
	URLSpec(r"/pages/privacy", misc.Privacy, name="Privacy"),
	URLSpec(r"/pages/terms", misc.Terms, name="Terms"),
	URLSpec(r"/pages/contact", misc.Contact, name="Contact"),
    
    #Calendar
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
#    (r'/poll/(\w+)/(-1|\d+)/(\w+)/?', PollHandler),
#    (r'/poll/(\w+)/(-1|\d+)/?', Randomizer), #
#    (r'/get/(\w+)/?', PostGetter),
#    (r'/comment/(\w+)/(.+)/?', Comment),
#    (r'/post/(\w+)/(.+)/?', Post),
#    (r'/anon_comment/(\w+)/(.+)/?', Comment, {'anon':True}),
#    (r'/anon_post/(\w+)/(.+)/?', Post, {'anon':True}),
#    (r'/vote/(\w+)/?', VoteObject),
#    (r'/unvote/(\w+)/?', UnvoteObject),
#    (r'/flag/(\w+)/', FlagObject),
#    (r'/unflag/(\w+)/?', UnflagObject),
], 
                                      
    cookie_secret="CHANGE THIS EVENTUALLY",
    login_url= "/auth/login/",
    static_path= os.path.join(os.path.dirname(__file__), "res", "static")
)

#Add methods to the template environment
globals = handlers.env.env.globals
globals['reverse_url'] = application.reverse_url
globals['css'] = lambda path: ("/static/css/" + path).replace("//", "/")
globals['script'] = lambda path: ("/static/scripts/" + path).replace("//", "/")
globals['image'] = lambda path: ("/static/images/" + path).replace("//", "/")

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()