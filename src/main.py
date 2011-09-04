import os.path

import tornado.ioloop
import tornado.web


from forms import *
from pymongo.errors import *

from jinja2 import Environment, PackageLoader
from db import *

from collections import defaultdict

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
        posts = get_top_posts_for_event(eventid, 3)
        self.write(self.template.render(posts=posts))   
        
        
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
        
class PostsHandler(BaseHandler):    
    #{ post_id:[list of callbacks] }
    callbacks = defaultdict(list)
    
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self, postid):
        #Start async listen
        self.wait_for_update(postid, self.on_update)
        #Return to the IOLoop until we are called back
        
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self, postid):
        """
        Will write out one of following to all connections listening on this post:
        --------------------    
        upvote_post
            postid
            
        downvote_post
            postid
            
        upvote_comment
            postid
            commentid
        
        downvote_comment
            postid
            commentid
            
        create_comment_for_post
            postid
        ----------------------    
        Semantics:
            <action name>
                <keyword>
                
        Syntax: 
            JSON, ex: {action:'update_post', postid:'1234'}
        
        The javascript client uses this information to update the screen in real time
        """
        cls = PostsHandler
        params = self.get_params()
        if not ('action' in params and 'postid' in params and 'userid' in params):
            self.set_status(400)
            self.finish("Error, improper params: " + str(params))
           
        #The post parameters will select one of the following functions
        actions = {
            'upvote_post':upvote_post,
            'downvote_post':downvote_post,
            'upvote_comment':upvote_comment,
            'downvote_comment':downvote_comment,
            'create_comment_for_post':create_comment_for_post 
        }
                
        action = params.pop('action') #Pop action from params because Mongo does not expect the 'action' keyword
        postid = params['postid']
        try:
            actions[action](**params) #Execute the database action with Mongo call, TODO:Make it nonblocking         
        except Exception as e:
            self.set_status(500)
            self.finish("Error, got: " + e.message)
            return
        
        #If no exception, push the results
        for callback in cls.callbacks[postid]:
            callback(action=action, **params)
            
        #Reset the callbacks
        del cls.callbacks[postid]
        
        #Done
        self.finish("Success")

    def wait_for_update(self, postid, callback):
        cls = PostsHandler
        #Register the callback
        cls.callbacks[postid] += [callback]
    
    def on_update(self, **json_response):
        if self.request.connection.stream.closed():
            return
        else:
            self.finish(json_response)

        
class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie('userid')
        self.redirect('/login/')

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
    (r'/posts/(.*)/?', PostsHandler),
    (r'/postforms/(change)/(\w+)/?', PostFormsHandler),
    (r'/postforms/(make)/?', PostFormsHandler),
    (r'/commentforms/(change)/(\w+)/(\d+.\d+)/?', CommentFormsHandler),
    (r'/commentforms/(make)/(\w+)/?', CommentFormsHandler),
    (r'/viewposts/(.*)/?', ViewPostsHandler)
    
], 
    cookie_secret="CHANGE THIS EVENTUALLY",
    login_url= "/login/",
    static_path= os.path.join(os.path.dirname(__file__), "res", "static")
)



if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()