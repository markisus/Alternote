import os.path

import tornado.ioloop
import tornado.web


from forms import *
from pymongo.errors import DuplicateKeyError

from jinja2 import Environment, PackageLoader
from db import *
from db.utils import __make_unique_string as mus
from collections import defaultdict

import json

env = Environment(loader=PackageLoader('res', 'templates'))

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        session = self.get_cookie('session', None)
        if not session: return None
        return db_get_userid(session)
    
    def __unpack_params(self, adict):
        """Tornado encapsulates HTTP params within list objects (idk why)
        so we need this method to unpack them"""
        unpacked = dict()
        for param in adict.keys():
            unpacked[param] = adict[param][0]
        return unpacked
    
    def get_params(self):
        return self.__unpack_params(self.request.arguments)
    
class ViewPostsHandler(BaseHandler):
    template = env.get_template('view_posts.template')
    
    @tornado.web.authenticated
    def get(self, eventid):
        get_event(eventid)
        posts = get_top_posts_for_event(eventid)
        self.write(self.template.render(posts=posts, eventid=eventid))   
        
        
class UserHandler(BaseHandler):
    template = env.get_template('user.template')
    
    @tornado.web.authenticated
    def get(self, userid=None):
        if not userid:
            userid = self.get_current_user()
        user = get_user(userid)
        self.write(self.template.render(user=user))


class ClassHandler(BaseHandler):
    template = env.get_template('class.template')
    
    #@tornado.web.authenticated
    def get(self, classid):
        aclass = get_class(classid)
        self.write(self.template.render(Class=aclass))
        
class ClassSearch(BaseHandler):
    template = env.get_template('class_search.template')
    
    @tornado.web.authenticated
    def get(self):
        form = ClassSearchForm()
        self.write(self.template.render(form=form))
    
    @tornado.web.authenticated
    def post(self):
        form = ClassSearchForm(**self.get_params())
        user = get_user(self.get_current_user())
        if form.validate():
            tags = form.tags.data.lower().split(" ")
            university = user['university']
            self.write(str(tags))
            results = search_classes(university, tags)
            for result in results:
                self.write(str(result) + "</br>")
        else:
            self.write(self.template.render(form=form))
        
class EventHandler(BaseHandler):
    template = env.get_template('event.template')
    
    @tornado.web.authenticated
    def get(self, classid):
        events = get_events_for_class(classid)
        self.write(self.template.render(events=events))
        
            
class RegistrationHandler(BaseHandler):
    template = env.get_template('registration.template')
    
    def get(self):
        form = RegistrationForm()
        self.write(self.template.render(form=form))
        
    def post(self):
        form = RegistrationForm(**self.get_params())
        if form.validate():
            try:
                userid = create_user(form.first_name.data,
                         form.last_name.data, 
                         form.password.data, 
                         form.email.data, 
                         form.university.data)
            except DuplicateKeyError as e:
                self.write(e.message)
                return
            self.set_secure_cookie('userid', userid)
            self.write("Registered")
        else:
            self.write(self.template.render(form=form))

class PostFormsHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self, action, postid=None):
        if action == "change":
            form = ChangePostForm(userid=self.get_current_user(), postid=postid)
            self.write(env.get_template('change_post.template').render(form=form))
        elif action == "make":
            self.write("Not Implemented")
            #form = MakePostForm(userid=self.get_current_user(), postid=postid)
            #self.write(env.get_template('make_post.template').render(form=form))
            
class CommentFormsHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self, action, postid=None, commentid=None):
        if action == "change":
            form = ChangeCommentForm(userid=self.get_current_user(), postid=postid, commentid=commentid)
            self.write(env.get_template('change_comment.template').render(form=form))
        elif action == "make":
            form = MakeCommentForm(userid=self.get_current_user(), postid=postid)
            self.write(env.get_template('make_comment.template').render(form=form))

class LoginHandler(BaseHandler):
    template = env.get_template('login.template')

    def get(self):
        form = LoginForm()
        
        userid = self.get_current_user()
        if userid:
            self.write("Note: You are already logged in as " + userid)
            
        self.write(self.template.render(form=form))

    def post(self):
        form = LoginForm(**self.get_params())
        if form.validate():
            try:
                user = get_user(form.email.data)
            except KeyError:
                self.write("No username or wrong password")
                return
            if user['password'] == form.password.data:
                session = db_login(user['_id'])
                self.set_cookie('session', session)
                self.redirect('/me/')
                return
            
            else:
                self.write("No username or wrong password")
        self.write(self.template.render(form=form))
    
    def delete(self):
        self.set_secure_cookie('userid', None)
        
class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie('userid')
        self.redirect('/login/')


#/poll/(eventid)
#/get/(eventid)

#/comment/(postid)/(message)
#/upvote/comment/(postid)/(commentid)
#/downvote/comment/(postid)/(commentid)

#/post/(eventid)/(message)
#/upvote/post/(postid)
#/downvote/post/(postid)

class Registry(object): #TODO: Implement singleton (?)
    def __init__(self):
        self.listeners = defaultdict(list)
        self.cache = defaultdict(list)
        self.count = 0
    
    def register_listener_on_event(self, listener, eventid):
        self.listeners[eventid].append(listener)
        
    def notify_all_listeners_about_event(self, eventid, data):
        eventid = str(eventid)
        self.cache[eventid].append(data)
        for listener in self.listeners[eventid]:
            listener.notify(json.dumps(self.cache[eventid]))
        self.listeners[eventid] = list() 
        
EVENT_REGISTRY = Registry()

class Listener(BaseHandler):
    def notify(self, data):
        if self.request.connection.stream.closed():
            return
        self.write(data)
        self.finish()
        
#/poll/(eventid)
class Randomizer(BaseHandler):
    @tornado.web.authenticated
    def get(self, eventid):
        self.redirect('/poll/' + str(eventid) + '/' + str(mus()))
        
#/poll/(eventid)/(randomid)
class PollHandler(Listener):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def get(self, eventid, connection=None):
        if not connection:
            self.redirect('/poll/' + str(eventid) + '/' + str(mus()))
            #We need to randomize the URL so that poll does not block subsequent connections
        #Register ourselves with the EVENT_REGISTRY
        EVENT_REGISTRY.register_listener_on_event(self, eventid)
        #Fall back to the ioloop and wait for self.notify to be called

#/get/(eventid)
class PostGetter(BaseHandler):
    @tornado.web.authenticated
    def get(self, eventid):
        posts = get_top_posts_for_event(eventid)
        self.write(str(list(posts)))
        
#/comment/(postid)/(message)
class Comment(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid, message):
        post = get_post(postid) #This can be sped up, no reason to get the entire post, also, handle erros better
        eventid = post['event']
        userid = self.get_current_user()
        
        create_comment_for_post(userid, postid, message)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid, "comment %s %s %s" % (userid, postid, message))

#/upvote/comment/(postid)/(commentid)        
class UpvoteComment(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid, commentid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        upvote_comment(userid, postid, commentid)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid, "upvote_comment %s %s %s" % (userid, postid, commentid))
        
#/downvote/comment/(postid)/(commentid)
class DownvoteComment(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid, commentid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        downvote_comment(userid, postid, commentid)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid, "downvote_comment %s %s %s" % (userid, postid, commentid))        
        
#/post/(eventid)/(message)
class Post(BaseHandler):
    @tornado.web.authenticated
    def get(self, eventid, message):
        userid = self.get_current_user()
        
        create_post_for_event(userid, eventid, message)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid, "post %s %s %s" % (userid, eventid, message))
        
#/upvote/post/(postid)
class UpvotePost(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        upvote_post(userid, postid)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid, "upvote_post %s %s" % (userid, postid))
        
#/downvote/post/(postid)
class DownvotePost(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        downvote_post(userid, postid)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid, "downvote_post %s %s" % (userid, postid))
    
application = tornado.web.Application([
    (r"/", LoginHandler),
    (r'/register/?', RegistrationHandler),
    (r'/me/?', UserHandler),
    (r'/users/(.*)/?', UserHandler),
    (r'/classes/?', ClassSearch),
    (r'/classes/(.*)/?', ClassHandler),
    (r'/events/(.*)/?', EventHandler),
    (r'/login/?', LoginHandler),
    (r'/logout/?', LogoutHandler),

    #SERVER API METHODS
        #/poll/(eventid)
        #/get/(eventid)
        
        #/comment/(postid)/(message)
        #/upvote/comment/(postid)/(commentid)
        #/downvote/comment/(postid)/(commentid)
        
        #/post/(eventid)/(message)
        #/upvote/post/(postid)
        #/downvote/post/(postid)
    (r'/poll/(\w+)/(\d+.\d+)?', PollHandler),
    (r'/poll/(\w+)/?', Randomizer),
    (r'/get/(\w+)/?', PostGetter),
    (r'/comment/(\w+)/(.+)/?', Comment),
    (r'/upvote/comment/(\w+)/(\d+.\d+)/?', UpvoteComment),
    (r'/downvote/comment/(\w+)/(\d+.\d+)/?', DownvoteComment),
    (r'/post/(\w+)/(.+)/?', Post),
    (r'/upvote/post/(\w+)/?', UpvotePost),
    (r'/downvote/post/(\w+)/?', DownvotePost),
    #END SERVER API METHODS
    
    (r'/viewposts/(.*)/?', ViewPostsHandler)
    
], 
    cookie_secret="CHANGE THIS EVENTUALLY",
    login_url= "/login/",
    static_path= os.path.join(os.path.dirname(__file__), "res", "static")
)



if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()