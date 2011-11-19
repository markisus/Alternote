from pymongo import Connection, ASCENDING
from pymongo.errors import *
from bson.objectid import ObjectId
from random import randint
from time import time
from datetime import datetime
from collections import *

def __author_query(userid):
    result = users.find_one({'_id':userid}, {'_id':1, 'first_name':1, 'last_name':1, 'type':1})
    if result == None:
        raise KeyError("No user with key " + str(userid) + " exists")
    return result

def __class_query(classid):
    classdoc = classes.find({'_id':classid}, {'name':1, '_id':1}, limit=1).hint([('_id',1), ('name',1)])[0]
    if classdoc == None:
        raise KeyError("Registration failed; could not find class with key " + classid)
    return classdoc

def create_class(university, instructor, name, section, finish_date):
    tags = name.lower().split(" ")
    return classes.insert(
                   {'_id':'-'.join((university,name,section)),
                    'university':university, 
                    'instructor':instructor, 
                    'name':name,
                    'section':section,
                    'finish_date':finish_date,
                    'tags':tags
                    }
                   , safe = True
                   )

def get_class(classid):
    result = classes.find_one({'_id':classid})
    if result == None:
        raise KeyError("No class with key " + str(classid) + " exists")
    return result

def create_user(first_name, last_name, password, email, university, classes=[], type="student"):
    return users.insert(
                 {'_id':email,
                  'first_name':first_name,
                  'last_name':last_name,
                  'email':email,
                  'university':university,
                  'classes':classes,
                  'password':password,
                  'type':type,
                  'flagged':[],
                  'voted':[],
                  'anonymous_items':[],
                  }
                 , safe = True
                )
    
def register_user_for_class(userid, classid):
    classdoc = classes.find({'_id':classid}, {'name':1, '_id':0}, limit=1).hint([('_id',1), ('name',1)])[0]
    if classdoc == None:
        raise KeyError("Registration failed; could not find class with key " + classid)
    
    class_name = classdoc['name']
    users.update( 
                 {'_id':userid}, 
                 {'$addToSet': 
                    {'classes':__class_query(classid)}
                }
            )

def create_event_for_class(classid, typ, location, start_time, end_time, details):
    return events.insert(
                    {'type':typ,
                     'class':__class_query(classid),
                     'location':location,
                     'start_time':start_time,
                     'end_time':end_time,
                     'details':details
                    }
                  , safe = True
                  )

def get_events_for_class(classid):
    return events.find({'class._id':classid})
def get_user(userid): #Todo: Consolidate this method with duplicate method "__author_query"
    result = users.find_one({'_id':userid})
    if result == None:
        raise KeyError("No user with key " + str(userid) + " exists")
    return result

def record_anon_item(userid, objectid):
    objectid = ObjectId(objectid)
    users.insert({'_id':userid}, {"$addToSet":{"anonymous_items":objectid}})
    
#Get the user object with only the info we need for display purposes
def get_user_display_info(userid, anon=False):
    print("Getting user disiplay info, anon: " + str(anon))
    result = users.find_one({'_id':userid}, {'_id':1, 'first_name':1, 'last_name':1, 'type':1}) #TODO: Index type for covered query?
    if result == None:
        raise KeyError("No user with key " + str(userid) + " exists")
    if anon:
        anonymize(result)
    print(result)
    return result

def get_event(eventid):
    eventid = ObjectId(eventid)
    result = events.find_one({'_id':eventid})
    if result == None:
        raise KeyError("No event with key " + str(eventid) + " exists")
    return result

def get_post(postid):
    postid = ObjectId(postid)
    result = events.posts.find_one({'_id':postid})
    if result == None:
        raise KeyError("No post with key " + str(postid) + " exists")
    return result

def get_eventid_of_object(objectid):
    result = get_eventid_of_post(objectid) or get_eventid_of_comment(objectid)
    if result == None:
        raise KeyError("No object with key " + str(objectid) + " exists")
    return result

def get_eventid_of_post(postid):
    postid = ObjectId(postid)
    result = events.posts.find_one({'_id':postid}, {'_id':0, 'event':1})
    if result != None:
        return result['event']


def get_eventid_of_comment(commentid):
    commentid = ObjectId(commentid)
    result = events.posts.find_one({'comments._id':commentid}, {'event':1})
    if result != None:
        return result['event']


def create_post_for_event(userid, eventid, post, anonymous=False):
    timestamp=datetime.now().isoformat()
    author = __author_query(userid)
    if anonymous: #Wipe identifying info
        anonymize(author)
    result = posts.insert(
                 {'message':post,
                  'votes':0,
                  'flags':0,
                  'event':ObjectId(eventid),
                  'author':author,
                  'comments':[],
                  'timestamp':timestamp,
                  }
                 )
    if anonymous: 
        record_anon_item(userid, result)
    return str(result)

def get_top_posts_for_event(eventid):
    eventid = ObjectId(eventid)
    return posts.find({'event':ObjectId(eventid)}).sort('timestamp', direction=ASCENDING).hint([('event',1),('timestamp',1)])

def __make_unique_string():
    return (str(time()) + str(randint(0, 999))).replace(".", "_") #Since Tornado is single threaded, we prob dont need the random

def anonymize(author):
    author['_id'] = "Anonymous"
    author['first_name'] = "Anonymous"
    author['last_name'] = "" 
    author['type'] = "student"
    return author

def create_comment_for_post(userid, postid, comment, anonymous=False):
    timestamp=datetime.now().isoformat()
    postid = ObjectId(postid)
    comment_id = ObjectId()
    author = __author_query(userid)
    if anonymous: #Wipe identifying info
        anonymize(author)
        record_anon_item(userid, comment_id)
        #Save this commentid into the user
    comment = {
                'message':comment,
                'votes':0,
                'flags':0,
                'timestamp':timestamp,
                'author':author,
                '_id':comment_id
               }
        
    posts.update({'_id':postid, 'comments._id':{'$ne':comment_id}},
                  {'$push': {'comments':comment}},
              )
        
    return str(comment_id) #Comment id unique within a post

def __create_vote_info(userid, type, timestamp):
    return {'userid':userid, 'timestamp':timestamp, 'type':type}

def get_user_votes_and_flags(userid):
    try:
        result = users.find({'_id':userid}, {'_id':0, 'voted':1, 'flagged':1}, limit=1).hint(
                               [('_id',1), ('voted',1), ('flagged', 1)]
                        )[0] #covered query
    except IndexError:
        raise KeyError("No user with key " + str(userid) + " exists")
    
    return result


def get_user_votes(userid):
    try:
        result = users.find({'_id':userid}, {'_id':0, 'voted':1}, limit=1).hint(
                               [('_id',1), ('voted',1), ('flagged', 1)]
                        )[0] #covered query
    except IndexError:
        raise KeyError("No user with key " + str(userid) + " exists")

    return result['voted']

def get_user_flags(userid):
    try:
        result = users.find({'_id':userid}, {'_id':0, 'flagged':1}, limit=1).hint(
                               [('_id',1), ('flagged',1)]
                        )[0] #covered query
    except IndexError:
        raise KeyError("No user with key " + str(userid) + " exists")
    print(result)
    return result['flagged']

def vote_object(userid, objectid):
    objectid = ObjectId(objectid)
    voted = get_user_votes(userid)
    if objectid in voted:
        print(str(objectid) + "is in voted")
        raise ValueError("Double-vote detected on object " + str(objectid))
    vote_post(userid, objectid)
    vote_comment(userid, objectid)
    users.update({"_id":userid}, {"$addToSet":{"voted":objectid}})

def unvote_object(userid, objectid):
    objectid = ObjectId(objectid)
    voted = get_user_votes(userid)
    if objectid not in voted:
        raise ValueError("Cannot unupvote before upvote on object " + str(objectid))
    unvote_post(userid, objectid)
    unvote_comment(userid, objectid)
    users.update({"_id":userid}, {"$pull":{"voted":objectid}})

def flag_object(userid, objectid):
    objectid = ObjectId(objectid)
    flagged = get_user_flags(objectid)
    if objectid in flagged:
        raise ValueError("Double-flag detected on object " + str(objectid))    
    flag_post(userid, objectid)
    flag_comment(userid, objectid)
    users.update({"_id":userid}, {"$addToSet":{"flagged":objectid}})

def unflag_object(userid, objectid):
    objectid = ObjectId(objectid)
    flagged = get_user_flags(userid)
    if objectid not in flagged:
        raise ValueError("Cannot unflag before flag on object " + str(objectid))
    unflag_post(userid, objectid)
    unflag_comment(userid, objectid)
    users.update({"_id":userid}, {"$pull":{"flagged":objectid}})


def vote_post(userid, postid, times=1): 
    timestamp=datetime.now().isoformat()
    posts.update({"_id":postid}, {"$inc":{"votes":times}})
    
def unvote_post(userid, postid, times=1):
    timestamp=datetime.now().isoformat()
    posts.update({"_id":ObjectId(postid)}, {"$inc":{"votes":-times}})

def vote_comment(userid, commentid, times=1):
    timestamp=datetime.now().isoformat()
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.votes":times}})

def unvote_comment(userid, commentid, times=1):
    timestamp=datetime.now().isoformat()
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.votes":-times}})
    
def flag_post(userid, postid, times=1):
    timestamp=datetime.now().isoformat()
    posts.update({"_id":postid}, {"$inc":{"flags":times}})
    
def unflag_post(userid, postid, times=1):
    timestamp=datetime.now().isoformat()
    posts.update({"_id":postid}, {"$inc":{"flags":-times}})
    
def flag_comment(userid, commentid, times=1):
    timestamp=datetime.now().isoformat()
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.flags":times}})
        
def unflag_comment(userid, commentid, times=1):
    timestamp=datetime.now().isoformat()    
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.flags":-times}})

##############################################################################
# End Real Time Server Methods                                               #
##############################################################################

def db_login(userid):
    session = __make_unique_string()
    logins.insert({'_id':session, 'userid':userid})
    return session

def db_logout(session):
    logins.remove({'_id':session})

def db_get_userid(session):
    user = logins.find_one({'_id':session})
    if not user:
        raise KeyError("No user matching this session " + session)
    return user['userid']