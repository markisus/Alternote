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
import datetime
from handlers.calendar import time_format, twelve_hour_time
import handlers.backbone

login_url = r"/auth/login"

application = tornado.web.Application([
    URLSpec(r"/", misc.LandingPage, name="LandingPage"),
    URLSpec(r"/registration/professor", registration.ProfessorRegistration, name="ProfessorRegistration"),
    URLSpec(r"/registration/standard", registration.RegularRegistration, name="RegularRegistration"),
    
    #Auth
    URLSpec(login_url, auth.LoginHandler, name="LoginHandler"),
    URLSpec(r"/auth/logout", auth.LogoutHandler, name="LogoutHandler"),
    
    #Admin Methods
    URLSpec(r"/admin/school/create", admin.CreateSchool, name="CreateSchool"),
    
    #Calendar
    URLSpec(r"/calendar/view/(?P<class_id>[\w|\-|%]+)", calendar.ViewCalendar, name="ViewCalendar"),
    URLSpec(r"/calendar/feed/(?P<class_id>[\w|\-|%]+)", calendar.CalendarFeed, name="CalendarFeed"),
    URLSpec(r"/calendar/details/(?P<class_id>[\w|\-|%]+)/(?P<calendar_id>\w+)", calendar.CalendarDetails, name="CalendarDetails"),
    URLSpec(r"/calendar/create/(?P<class_id>[\w|\-|%]+)", calendar.CreateCalendarStandalone, name="CreateCalendarStandalone"),
    
    #Classes
    URLSpec(r"/classes/create", classes.CreateClass, name="CreateClass"),
    URLSpec(r"/classes/view", classes.ViewClasses, name="ViewClasses"),
    URLSpec(r"/classes/codes/(?P<class_id>[\w|\-|%]+)", classes.ViewCodes, name="ViewCodes"),

    #Files
    URLSpec(r"/files/edit/(?P<class_id>[\w|\-|%]+)", files.Files, name="Files"),
    URLSpec(r"/files/delete/(?P<class_id>[\w|\-|%]+)", files.FileDelete, name="FileDelete"),
    URLSpec(r"/files/tags/(?P<class_id>[\w|\-|%]+)/(?P<record_id>\w+)", files.FileTags, name="FileTags"),
    
	#Pages
	URLSpec(r"/pages/about", misc.About, name="About"),
	URLSpec(r"/pages/privacy", misc.Privacy, name="Privacy"),
	URLSpec(r"/pages/terms", misc.Terms, name="Terms"),
	URLSpec(r"/pages/contact", misc.Contact, name="Contact"),
    
    #Test
    
    #Backbone Bootstrap
    URLSpec(r"/class/(?P<class_id>[\w|\-|%]+)", handlers.backbone.Bootstrap, name="Bootstrap"),
    #Backbone Collection URLs
    URLSpec(r"/events/(?P<class_id>[\w|\-|%]+)", handlers.backbone.Events, name="Events"),
    URLSpec(r"/events/(?P<class_id>[\w|\-|%]+)/(?P<event_id>\w+)", handlers.backbone.Events, name="Event"),
    
    #Backbone.js Model URLs
#    URLSpec(r"/class/(?P<class_id>[\w|\-|%]+)", X, name="Class"),
#    URLSpec(r"/file/(?P<class_id>[\w|\-|%]+)/(?<file_id>\w+)", X, name="File"),
#    URLSpec(r"/event/(?P<class_id>[\w|\-|%]+)", X, name="Event"),
#    URLSpec(r"/post/(")
    #Backbone.js Collections
#    URLSpec(r"/files/(?P<class_id>[\w|\-|%]+)"),
#    URLSpec(r"/events/(?P<class_id>[\w|\-|%]+)"),
#    URLSpec(r"/posts/(?P<class_id>[\w|\-|%]+)"),
    
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
    static_path= static_path,
)

#Add methods to the template environment
globals = handlers.env.env.globals
globals['reverse_url'] = application.reverse_url
globals['css'] = lambda path: ("/static/css/" + path).replace("//", "/")
globals['script'] = lambda path: ("/static/scripts/" + path).replace("//", "/")
globals['image'] = lambda path: ("/static/images/" + path).replace("//", "/")
globals['file_path'] = lambda class_id, file_name: ("/static/files/" + class_id + "/" + file_name).replace("//", "/")
#Date formatter
def date_format(date_string):
    date_string = date_string[:10] #Lop off the hours and minutes
    my_date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
    return datetime.datetime.strftime(my_date, "%a, %m/%d")
#Add formatters to globals dict
globals['time_format'] = time_format
globals['date_format'] = date_format
globals['twelve_hour_time'] = twelve_hour_time
if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()