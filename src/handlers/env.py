#Things that all handlers need to access
from UserDict import UserDict
from jinja2 import Environment, PackageLoader
import tornado.web
from db.logins import db_get_userid, db_logout
import db.users
import os
import datetime
env = Environment(variable_start_string='[[', variable_end_string=']]', loader=PackageLoader('res', 'templates'))
prof_code = "alternote_rocks"


#Takes a Handler, checks if the user is prof
def check_prof(f):
    def wrapper(self, *args, **kwargs):
        #args[0] is self
        user = self.user = getattr(self, 'user', db.users.get_user(self.get_current_user()))
        if not user['type'] in ("professor", "admin"):
            self.write("Permission Denied")
            return
        else:
            return f(self, *args, **kwargs)
    return wrapper
                                                      
#UI Stuff
#Sidebar needs:
    #Instructors, Classmates
        #Class_id
    #Meeting Times
        #Class_id
    #Files
        #Class_id
    #Conversations
        #Class_id
    #Upcoming
        #Class_id
        
#Some custom logic for auth and param handling
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        session = self.get_cookie('session', None)
        if not session: return None
        try:
            return db_get_userid(session)
        except KeyError:
            #Database session cleared
            return None
        
    def __unpack_params(self, adict):
        """Tornado encapsulates HTTP params within list objects (idk why)
        so we need this method to unpack them"""
        unpacked = dict()
        for param in adict.keys():
            unpacked[param] = adict[param][0]
        return unpacked
    
    def get_params(self):
        #return self.__unpack_params(self.request.arguments)
        params = UserDict(self.request.arguments)
        params.getlist = lambda key:params[key] #wtforms needs this
        return params
        
    def render_sidebar(self, class_id):
        template = env.get_template('ui/sidebar.template')
        start = "0"
        finish = "9"
        now = datetime.datetime.now().isoformat()[:16]
        class_doc = db.classes.get_class(class_id)
    
        files = db.files.get_records(class_id)
        conversations = db.calendar.search_items(class_id, start, now)
        upcoming = db.calendar.search_items(class_id, now, finish, limit=10)
        return template.render(class_id=class_id, class_doc=class_doc, files=files, conversations=conversations, upcoming=upcoming)
    
    #Clean this up
    def render_navbar(self, class_id=None, priveledged=False, logged_in=True):
        template = env.get_template('ui/navbar.template')
        links = list()
        if class_id:
            links += [
                ('Calendar', self.reverse_url("ViewCalendar", class_id)),
                ]
            if priveledged:
                links += [
                    ('Files', self.reverse_url("Files", class_id)),
                    ('Codes', self.reverse_url("ViewCodes", class_id))
                    ]
        if logged_in:
            links += [
                  ('Choose Class', self.reverse_url("ViewClasses")),
                  #('Create Class', self.reverse_url("CreateClass")),
                  ('Logout', self.reverse_url("LogoutHandler")),
            ]
        return template.render(class_id=class_id, links=links, logged_in=logged_in)
    