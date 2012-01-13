import tornado
from db.logins import *
from db.conversations import *
import db.conversations
from collections import defaultdict
import json
from backbone import collection_to_Backbone
from env import BaseHandler
import smtplib
from email.mime.text import MIMEText

class JSONPHandler(BaseHandler):
    def write(self, eventid, chunk):
        #Kind of a kludge... :(
        BaseHandler.write(self, 'events.get("'+ eventid +'").get_client().callback(' + str(chunk) + ')')

class Cache(object):
    def __init__(self):
        self.size = 50
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
        return data
    
    def get_last_item(self):
        return self.update_counter - 1

class Registry(object): #TODO: Implement singleton (?)
    def __init__(self):
        self.listeners = defaultdict(list)
        self.caches = defaultdict(Cache)

    def register_listener_on_event(self, eventid, listener):
        eventid = str(eventid)
        print("\tAppending listener to event")
        self.listeners[eventid].append(listener)
        print("Done")
    
    def add_datum_to_event_cache(self, eventid, datum):
        eventid = str(eventid)
        self.caches[eventid].add(datum)


    def notify_all_listeners_about_event(self, eventid):
        eventid = str(eventid)
        for listener in self.listeners[eventid]:
            listener.notify(eventid, self.caches[eventid])
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

class Listener(JSONPHandler):     
    
    def set_cutoff(self, cutoff):
        self.cutoff = cutoff
    
    def notify(self, eventid, cache):
        if self.request.connection.stream.closed():
            return
        try:
            data = cache.get_recent_data(self.cutoff) #inclusive of cutoff
        except KeyError as e:
            #The oldest item should have been checked when the cutoff was set
            #Items cannot be deleted from the tail of the cache without notifying all listeners
            self.set_status(410) #Gone
            self.finish()
            return
        #Reveal anon author
        for datum in data.values():
            if datum['action'] in ['post', 'comment']:
                if datum['user']['_id'] == 'Anonymous':
                    datum['is_author'] = db.conversations.is_anon_author(self.get_current_user(), datum['objectid'])
                else:
                    datum['is_author'] = datum['user']['_id'] == self.get_current_user()
#        print("Revealed anon post: " + str(post))
        self.write(eventid, json.dumps(data, default=str, cls=None))
        self.finish()
        
#/poll/(eventid)/(last_received_item)
class Randomizer(BaseHandler):
    @tornado.web.authenticated
    def get(self, eventid, last_received_item):
        #We need to do a redirect to a unique url so that the browser opens up a socket for this connection
        self.redirect('/poll/' + str(eventid) + '/' + last_received_item + '/' + str(ObjectId()))
        
#/poll/(eventid)/(last_received_message)/(randomid)
class PollHandler(Listener):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def get(self, eventid, last_received_message, connection):
        print("\nInside poll of event: " + eventid)
        oldest_item_index = EVENT_REGISTRY.get_oldest_index_in_cache_for_eventid(eventid)
        print("Oldest item in cache is " + str(oldest_item_index))
        print("Client's last received message is " + str(last_received_message))
        if last_received_message < oldest_item_index:
            print("Client's message is too old... he should refresh the page")
            self.set_status(410) #Gone - Client's last received message is too old
            self.finish()
            return
        
        self.set_cutoff(int(last_received_message) + 1) #We want to receive updates that are numbered strictly greater than our last update
        #If the cache already has newer elements, we can immediately update
        newest_item_index = EVENT_REGISTRY.get_newest_index_in_cache_for_eventid(eventid)
        print(newest_item_index)
        if newest_item_index >= self.cutoff:
            print("New events in cache, no need for listen...")
            self.notify(eventid, EVENT_REGISTRY.caches[eventid])
            return
        
        print("No new events, registering to listen...")
        #Register ourselves with the EVENT_REGISTRY
        EVENT_REGISTRY.register_listener_on_event(eventid, self)
        print("Poll finished")
        #Fall back to the ioloop and wait for self.notify to be called

#/get/(eventid)
class PostGetter(JSONPHandler):
    @tornado.web.authenticated
    def get(self, eventid):
        posts = get_top_posts_for_event(eventid)
        #Find anon stuff and mark the current user as the true author if he is
        #reveal
        posts = [self.reveal_author(p) for p in posts]
        #to backbone...
#        print(posts)
        collection_to_Backbone(posts)
        userid = self.get_current_user()
        votes_and_flags = get_user_votes_and_flags(userid)
        last_element = EVENT_REGISTRY.get_newest_index_in_cache_for_eventid(eventid)
        #the js client expects a dictionary of actions, so we wrap the dictionary in another dictionary
        result = {-1: {'action':'get', 'last_element':last_element, 'posts':posts, 'votes_and_flags':votes_and_flags}}
#        print("Sending result: " + str(result))
        self.write(eventid, json.dumps(result,  default=str, cls=None))
       
#/comment/(postid)/(message)
class Comment(BaseHandler):
    def initialize(self, anon=False):
        self.anon = anon
        
    @tornado.web.authenticated
    def get(self, postid, message):
        print("Comment received: " + message)
        eventid = get_eventid_of_post(postid)
        userid = self.get_current_user()
        user = get_user_display_info(userid, self.anon)
            
        comment = create_comment_for_post(userid, postid, message, self.anon)
        self.reveal_author(comment)
        
        datum = {
                 'action':'comment', 
                 'user':user, 
                 'parent_id':postid, 
                 'message':comment['message'], 
                 'objectid':str(comment['_id']),
#                 'is_author':comment['is_author'],
                 'timestamp':comment['timestamp']
                 }
        
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)

#/post/(eventid)/(message)
class Post(BaseHandler):
    def initialize(self, anon=False, email=False):
        print("Initializing post!")
        self.anon = anon
        self.email = email
        
    @tornado.web.authenticated
    def get(self, eventid, message):
        print("**Post received: " + message)
        userid = self.get_current_user()
        user = get_user_display_info(userid, self.anon)
        
        post = create_post_for_event(userid, eventid, message, self.anon)
        self.reveal_author(post)
        
        datum = {
                 'action':'post', 
                 'user':user, 
                 'message':post['message'], 
                 'objectid':str(post['_id']), 
#                 'is_author':post['is_author'],
                 'timestamp':post['timestamp']
                 }
        
        print("Adding post to event cache")
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        print("notifying listeners")
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)

        if self.email:
            #Get the class_id associated with this event
            event_id = post["event_id"]
            class_id = get_event(event_id)['class']['_id']
            class_doc = db.classes.get_class(class_id)
            instructor_emails = [instructor['_id'] for instructor in class_doc['instructors']]
            ta_emails = [ta['_id'] for ta in class_doc['tas']]
            student_emails = [student['_id'] for student in class_doc['students']]
            #Make sure that the current user is in instructors or tas
            if self.get_current_user() in instructor_emails+ta_emails:
                print("Emailing...")
                msg = MIMEText(message)
                msg['Subject'] = class_doc['name'] + ": " + message[:20] + "..."
                msg['From'] = "hello@alternote.com"
                msg['To'] = student_emails
                msg['Cc'] = instructor_emails + ta_emails
                s = smtplib.SMTP('localhost')
                s.sendmail("hello@alternote.com", student_emails + instructor_emails + ta_emails, msg.as_string())
                print("Done...")
            else:
                raise ValueError("Not priveleged, cannot email.")
#/delete/(messageid)/
class Delete(BaseHandler):
        
    @tornado.web.authenticated
    def get(self, message_id):
        print("Deleting...")
        userid = self.get_current_user()
        eventid = get_eventid_of_object(message_id)
        #Check if user is the author
        message = get_post(message_id)
        author_id = message['author']['_id']
        if author_id == 'Anonymous':
            if not is_anon_author(userid, message_id):
                raise ValueError(userid + " is not the author of " + message_id)
        elif author_id != userid:
            raise ValueError(userid + " is not the author of  " + message_id)

        delete_object(message_id)
        print("Delete success")
            
        
        datum = {
                 'action':'destroy', 
                 'objectid':message_id,
                 }
        
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
        
class VoteObject(BaseHandler):    
    @tornado.web.authenticated
    def get(self, objectid):
        print("Vote object!")
        eventid = get_eventid_of_object(objectid)
        userid = self.get_current_user()
        try:
            vote_object(userid, objectid)
        except ValueError as e:
            print(e.message)
            return
        datum = {'action':'vote', 'objectid':objectid, 'userid':userid}
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
        
class UnvoteObject(BaseHandler):    
    @tornado.web.authenticated
    def get(self, objectid):
        print("unvote object!")
        eventid = get_eventid_of_object(objectid)
        userid = self.get_current_user()
        try:
            unvote_object(userid, objectid)
        except ValueError as e:
            print(e.message)
            return
        datum = {'action':'unvote', 'objectid':objectid, 'userid':userid}
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
        
class FlagObject(BaseHandler):    
    @tornado.web.authenticated
    def get(self, objectid):
        print("flag object!")
        eventid = get_eventid_of_object(objectid)
        userid = self.get_current_user()
        try:
            flag_object(userid, objectid)
        except ValueError as e:
            print(e.message)
            return
        datum = {'action':'flag', 'objectid':objectid, 'userid':userid}
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)
        
class UnflagObject(BaseHandler):    
    @tornado.web.authenticated
    def get(self, objectid):
        eventid = get_eventid_of_object(objectid)
        userid = self.get_current_user()
        try:
            unflag_object(userid, objectid)
        except ValueError as e:
            print(e.message)
            return
        datum = {'action':'unflag', 'objectid':objectid, 'userid':userid}
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)