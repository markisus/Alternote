#Things that all handlers need to access
from UserDict import UserDict
from db.logins import db_get_userid, db_logout
from jinja2 import Environment, PackageLoader
from tornado.web import authenticated
import datetime
import db.users
import os
import tornado.web
import db.classes
from db.classes import unpack_userids
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
        links += [
              ('Choose Class', self.reverse_url("ViewClasses")),
              #('Create Class', self.reverse_url("CreateClass")),
              ('Logout', self.reverse_url("LogoutHandler")),
        ]
        return template.render(class_id=class_id, links=links)
    
#Use this handler for "in-class" pages
class ClassViewHandler(BaseHandler):
    
    def enforce_credentials(self, class_id):
        user_id = self.get_current_user()
        self.class_doc = db.classes.get_class(class_id)
        self.students = unpack_userids(self.class_doc['students'])
        self.tas = unpack_userids(self.class_doc['tas'])
        self.profs = unpack_userids(self.class_doc['instructors'])
        if user_id in self.profs:
            self.user_type = "professor"
        elif user_id in self.tas:
            self.user_type = "ta"
        elif user_id in self.students:
            self.user_type = "student"
        else:
            raise ValueError(user_id + " is not a member of " + class_id)

    @authenticated
    def get(self, class_id, *args, **kwargs):
        #Enforce credentials
        self.enforce_credentials(class_id)
        #Check if the request is IE
        #If it is IE - render complete
        if self.get_argument("ie", None):
            content = self.render_get(class_id, *args, **kwargs)
            out = self.render_frame(class_id, content=content)
        #Check if the request is ajax
        #If is, render partial
        elif self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            out = self.render_get(class_id, *args, **kwargs)
        #Else: Render frame
        else:
            out = self.render_frame(class_id)
        self.write(out)
        
    def post(self, class_id, *args, **kwargs):
        #Enforce credentials
        self.enforce_credentials(class_id)
        #Check if the request is IE
        #If it is IE - render complete
        if self.get_argument("ie", None):
            content = self.render_post(class_id, *args, **kwargs)
            out = self.render_frame(class_id, content=content)
        #Check if the request is ajax
        #If is, render partial
        elif self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            out = self.render_post(class_id, *args, **kwargs)
        #Else: Render frame (How would we ever get here with a post request (maybe user has no js)??)
        else:
            out = self.render_frame(class_id)
        self.write(out)
    
    #Override: return html string
    def render_post(self, *args, **kwargs):
        pass
    
    #Override: return html string
    def render_get(self, *args, **kwargs): 
        #Return the html string, rendered from template
        pass
    
    #Render frame expects enforce_credentials to be called before it to populate necessary variables like class_doc
    frame_template = env.get_template('class_view.template')
    def render_frame(self, class_id, content=None):
        start = "0"
        finish = "9"
        now = datetime.datetime.now().isoformat()[:16]
        files = db.files.get_records(class_id)
        conversations = db.calendar.search_items(class_id, start, now)
        upcoming = db.calendar.search_items(class_id, now, finish, limit=10)
        #Return the frame with content injected
        data = {'class_doc':self.class_doc,
                'class_id':class_id,
                'files':files,
                'upcoming':upcoming,
                'conversations':conversations,
                'user_type':self.user_type
                }
        if content:
            data.update({'content':content})    
        return self.frame_template.render(**data)
