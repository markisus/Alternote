import tornado
from db.logins import *
from db.conversations import *
from collections import defaultdict
import json
from backbone import collection_to_Backbone

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
        #to backbone...
#        print(posts)
        collection_to_Backbone(posts)
        userid = self.get_current_user()
        votes_and_flags = get_user_votes_and_flags(userid)
        last_element = EVENT_REGISTRY.get_newest_index_in_cache_for_eventid(eventid)
        #the js client expects a dictionary of actions, so we wrap the dictionary in another dictionary
        result = {-1: {'action':'get', 'last_element':last_element, 'posts':list(posts), 'votes_and_flags':votes_and_flags}}
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
        
        datum = {
                 'action':'comment', 
                 'user':user, 
                 'parent_id':postid, 
                 'message':message, 
                 'objectid':str(comment['_id']),
                 'timestamp':comment['timestamp']
                 }
        
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        EVENT_REGISTRY.notify_all_listeners_about_event(eventid)

#/post/(eventid)/(message)
class Post(BaseHandler):
    def initialize(self, anon=False):
        print("Initializing post!")
        self.anon = anon
        print("Anon post!")
        
    @tornado.web.authenticated
    def get(self, eventid, message):
        print("**Post received: " + message)
        userid = self.get_current_user()
        user = get_user_display_info(userid, self.anon)
        
        post = create_post_for_event(userid, eventid, message, self.anon)
        
        datum = {
                 'action':'post', 
                 'user':user, 
                 'message':message, 
                 'objectid':str(post['_id']), 
                 'timestamp':post['timestamp']
                 }
        print("Adding post to event cache")
        EVENT_REGISTRY.add_datum_to_event_cache(eventid, datum)
        print("notifying listeners")
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