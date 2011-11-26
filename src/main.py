from forms import *
from forms.forms import RegistrationCodeForm, ProfRegistrationForm
from handlers import admin, registration, classes, misc, auth, calendar, files
from jinja2 import Environment, PackageLoader
from tornado.web import URLSpec
import cgi
import json
import os.path
import tornado.ioloop
import tornado.web
import handlers
from constants import static_path

login_url = r"/auth/login"

application = tornado.web.Application([
    URLSpec(r"/", misc.LandingPage, name="LandingPage"),
    URLSpec(r"/registration/professor", registration.ProfessorRegistration, name="ProfessorRegistration"),
    
    #Auth
    URLSpec(login_url, auth.LoginHandler, name="LoginHandler"),
    URLSpec(r"/auth/logout", auth.LogoutHandler, name="LogoutHandler"),
    
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

    #Files
    URLSpec(r"/files/view/([\w|\-|%]+)", files.Files, name="Files"),
    URLSpec(r"/files/delete/([\w|\-|%]+)", files.FileDelete, name="FileDelete"),
    URLSpec(r"/files/tags/(\w+)", files.FileTags, name="FileTags"),
    
	#Pages
	URLSpec(r"/pages/about", misc.About, name="About"),
	URLSpec(r"/pages/privacy", misc.Privacy, name="Privacy"),
	URLSpec(r"/pages/terms", misc.Terms, name="Terms"),
	URLSpec(r"/pages/contact", misc.Contact, name="Contact"),
    
    #Test

    
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
    login_url= login_url,
    static_path= static_path
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