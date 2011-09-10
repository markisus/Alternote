import os.path

import tornado.ioloop
import tornado.web

from pymongo.errors import DuplicateKeyError

from jinja2 import Environment, PackageLoader
from db import *
from db.utils import __make_unique_string as mus
from collections import defaultdict

import json

from forms import *

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

class Cache(object):
    def __init__(self):
        self.size = 3
        self.update_counter = 0
        self.data = dict()
    
    def add(self, datum):
        self.data[self.update_counter] = datum
        self.update_counter += 1
        
        old_item_index = self.update_counter - self.size - 1
        if old_item_index in self.data.keys():
            del self.data[old_item_index]
    
    #Throws KeyError if you try to access old data (data that has been deleted)
    def get_recent_data(self, cutoff_index):
        keys = self.data.keys()
        if cutoff_index not in keys:
            raise KeyError("This key %d is no longer available" % cutoff_index)
        data = { i:self.data[i] for i in self.data.keys() if i >= cutoff_index }
        print("Getting recent data " + str(data))
        return data
    
    def get_last_item(self):
        return self.update_counter - 1

class Registry(object): #TODO: Implement singleton (?)
    def __init__(self):
        self.listeners = defaultdict(list)
        self.caches = defaultdict(Cache)
        self.cache_size = 50 #Number of messages to keep in cache, see self.add_datum_...
    
    def register_listener_on_event(self, eventid, listener):
        print("Appending a listener for " + str(eventid))
        eventid = str(eventid)
        self.listeners[eventid].append(listener)
        print("# of listeners now on this eventid: " + str(len(self.listeners[eventid])))
    
    def add_datum_to_event_cache(self, eventid, datum):
        eventid = str(eventid)
        self.caches[eventid].add(datum)

    def notify_all_listeners_about_event(self, eventid):
        eventid = str(eventid)
        print("Notifying all listeners...")
        for listener in self.listeners[eventid]:
            print("\tFound a listener...")
            listener.notify(self.caches[eventid])
        self.listeners[eventid] = list()
    
    def get_oldest_index_in_cache_for_eventid(self, eventid):
        eventid = str(eventid)
        cache = self.caches[eventid]
        old_item_index = cache.update_counter - cache.size
        if old_item_index < 0:
            old_item_index = -1
        return old_item_index
    
    def get_newest_index_in_cache_for_eventid(self, eventid):
        return self.caches[eventid].get_last_item()
        
EVENT_REGISTRY = Registry()

class Listener(BaseHandler):     
    
    def set_cutoff(self, cutoff):
        self.cutoff = cutoff
    
    def notify(self, cache):
        if self.request.connection.stream.closed():
            return
        try:
            data = cache.get_recent_data(self.cutoff) #inclusive of cutoff
        except KeyError as e:
            print("Warning: This should never happen!!" + e.message)
            self.set_status(410) #Gone
            self.finish()
            return
        self.write(json.dumps(data))
        self.finish()
        
#/poll/(eventid)/(last_received_item)
class Randomizer(BaseHandler):
    @tornado.web.authenticated
    def get(self, eventid, last_received_item):
        print("inside randomizer")
        #Check if the item being requested still exists in cache
        oldest_item_index = EVENT_REGISTRY.get_oldest_index_in_cache_for_eventid(eventid)
        print("oldest_item_index %d " % oldest_item_index)
        if last_received_item < oldest_item_index:
            self.set_status(410) #Gone
            self.finish()
            return
            
        print("redirecting...")
        self.redirect('/poll/' + str(eventid) + '/' + last_received_item + '/' + str(mus()))
        
#/poll/(eventid)/(last_received_message)/(randomid)
class PollHandler(Listener):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def get(self, eventid, last_received_message, connection):
        
        oldest_item_index = EVENT_REGISTRY.get_oldest_index_in_cache_for_eventid(eventid)
        print("oldest_item_index %d " % oldest_item_index)
        if last_received_message < oldest_item_index:
            self.set_status(410) #Gone
            self.finish()
            return
        
        print("inside pollhandler")
        self.set_cutoff(int(last_received_message) + 1)
        #Register ourselves with the EVENT_REGISTRY
        print("Registering a listener on " + str(eventid))
        EVENT_REGISTRY.register_listener_on_event(eventid, self)
        #Fall back to the ioloop and wait for self.notify to be called
        

#/get/(eventid)
class PostGetter(BaseHandler):
    @tornado.web.authenticated
    def get(self, eventid):
        posts = get_top_posts_for_event(eventid)
        last_element = EVENT_REGISTRY.get_newest_index_in_cache_for_eventid(eventid)
        result = {'last_element':last_element, 'posts':list(posts)}
        self.write(json.dumps(result,  default=str, cls=None))
        
#/comment/(postid)/(message)
class Comment(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid, message):
        post = get_post(postid) #This can be sped up, no reason to get the entire post, also, handle erros better
        eventid = post['event']
        userid = self.get_current_user()
        
        commentid = create_comment_for_post(userid, postid, message)
        
        #serialize the comment to get rid of spaces so that we can send a space delimited instruction to javascript
        message = message.replace("/", "/s")
        message = message.replace(" ", "/p")
        print("about to send message: " + str(message))

        EVENT_REGISTRY.add_datum_to_event_cache(eventid, "comment %s %s %s %s" % (userid, postid, commentid, message))
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)

#/upvote/comment/(postid)/(commentid)        
class UpvoteComment(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid, commentid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        upvote_comment(userid, postid, commentid)
        
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, "upvote_comment %s %s %s" % (userid, postid, commentid))
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
        
#/downvote/comment/(postid)/(commentid)
class DownvoteComment(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid, commentid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        downvote_comment(userid, postid, commentid)
        
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, "downvote_comment %s %s %s" % (userid, postid, commentid))  
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)        
        
#/post/(eventid)/(message)
class Post(BaseHandler):
    @tornado.web.authenticated
    def get(self, eventid, message):
        userid = self.get_current_user()
        
        postid = create_post_for_event(userid, eventid, message)
        
        message = message.replace("/", "/s")
        message = message.replace(" ", "/p")
        print("about to send message: " + str(message))
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, "post %s %s %s %s" % (userid, eventid, postid, message))
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
        
#/upvote/post/(postid)
class UpvotePost(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        upvote_post(userid, postid)
        
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, "upvote_post %s %s" % (userid, postid))
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
        
#/downvote/post/(postid)
class DownvotePost(BaseHandler):
    @tornado.web.authenticated
    def get(self, postid):
        post = get_post(postid)
        eventid = post['event']
        userid = self.get_current_user()
        
        downvote_post(userid, postid)
        
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, "downvote_post %s %s" % (userid, postid))
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
    
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
        #/poll/(eventid)/(last_received_item)
        #/get/(eventid)
        
        #/comment/(postid)/(message)
        #/upvote/comment/(postid)/(commentid)
        #/downvote/comment/(postid)/(commentid)
        
        #/post/(eventid)/(message)
        #/upvote/post/(postid)
        #/downvote/post/(postid)
    (r'/poll/(\w+)/(-?\d+)/(\d+.\d+)/?', PollHandler),
    (r'/poll/(\w+)/(-?\d+)/?', Randomizer),
    (r'/get/(\w+)/?', PostGetter),
    (r'/comment/(\w+)/(.+)/?', Comment),
    (r'/upvote/comment/(\w+)/(\d+.\d+)/?', UpvoteComment),
    (r'/downvote/comment/(\w+)/(\d+_\d+)/?', DownvoteComment),
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