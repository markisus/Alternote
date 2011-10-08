from pymongo import Connection, ASCENDING
from pymongo.errors import *
from bson.objectid import ObjectId
from random import randint
from time import time
from datetime import datetime

default_connection = ('localhost', 27017)
connection = Connection(*default_connection)
alternote = connection.alternote

#Binding collection names and setting indices
users = alternote.users
users.ensure_index([('_id',1), ('first_name',1), ('last_name',1)]) #For covered queries
users.ensure_index([('_id',1), ('flagged', 1)])
users.ensure_index([('_id',1), ('upvoted', 1), ('flagged', 1)])

events = alternote.events
events.ensure_index([('class._id',1)])

posts = alternote.events.posts
posts.ensure_index([('comment._id',1)])
posts.ensure_index([('event',1),('timestamp',1)])

#Ben will handle these, we can get rid of them later
classes = alternote.classes
posts.ensure_index([('_id',1), ('name',1)], [('university',1), ('tags',1)])

logins = alternote.logins
logins.ensure_index([('userid',1)])

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

def clean_collections():
    users.remove()
    events.remove()
    posts.remove()
    classes.remove()

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

##################################################################################################
# Ben will reimplement the above methods. The methods below are necessary to the real time server#
##################################################################################################
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

def get_eventid_of_post(postid):
    postid = ObjectId(postid)
    result = events.posts.find_one({'_id':postid}, {'_id':0, 'event':1})
    if result == None:
        raise KeyError("No post with key " + str(postid) + " exists")
    return result['event']

def get_eventid_of_comment(commentid):
    commentid = ObjectId(commentid)
    result = events.posts.find_one({'comments._id':commentid}, {'event':1})
    if result == None:
        raise KeyError("No comment with key " + str(commentid) + " exists")
    return result['event']


def create_post_for_event(userid, eventid, post, anonymous=False, timestamp=datetime.now().isoformat()):
    author = __author_query(userid)
    if anonymous: #Wipe identifying info
        anonymize(author)
    result = posts.insert(
                 {'post':post,
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

#Kind of convoluted, get rid of retry mechanism and hope that the comment succeeds
def create_comment_for_post(userid, postid, comment, anonymous=False, timestamp=datetime.now().isoformat()):
    postid = ObjectId(postid)
    comment_id = ObjectId()
    author = __author_query(userid)
    if anonymous: #Wipe identifying info
        anonymize(author)
        record_anon_item(userid, comment_id)
        #Save this commentid into the user
    comment = {
                'comment':comment,
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

def vote_post(userid, postid, timestamp=datetime.now().isoformat(), times=1): 
    postid = ObjectId(postid)
    #Check that this user has not voted yet
    voted = get_user_votes(userid)
    if postid in voted:
        raise ValueError("Double-vote detected on postid " + str(postid))
    
    posts.update({"_id":postid}, {"$inc":{"votes":times}})
    users.update({"_id":userid}, {"$addToSet":{"voted":postid}})
    
def unvote_post(userid, postid, timestamp=datetime.now().isoformat(), times=1):
    postid = ObjectId(postid)
    voted = get_user_votes(userid)
    if postid not in voted:
        raise ValueError("Cannot unupvote before upvote on postid " + str(postid))
    posts.update({"_id":ObjectId(postid)}, {"$inc":{"votes":-times}})
    users.update({"_id":userid}, {"$pull":{"voted":postid}})

def vote_comment(userid, commentid, timestamp=datetime.now().isoformat(), times=1):
    commentid = ObjectId(commentid)
    voted = get_user_votes(userid)
    if commentid in voted:
        raise ValueError("Double-vote detected on commentid " + str(commentid))
    
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.votes":times}})
    users.update({"_id":userid}, {"$addToSet":{"voted":commentid}})

def unvote_comment(userid, commentid, timestamp=datetime.now().isoformat(), times=1):
    commentid = ObjectId(commentid)
    voted = get_user_votes(userid)
    if commentid not in voted:
        raise ValueError("Cannot unupvote before upvote on commentid " + str(commentid))
    
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.votes":-times}})
    users.update({"_id":userid}, {"$pull":{"voted":commentid}})
    
def flag_post(userid, postid, timestamp=datetime.now().isoformat(), times=1):
    postid = ObjectId(postid)
    flagged = get_user_flags(userid)
    if postid in flagged:
        raise ValueError("Double-flag detected on postid " + str(postid))
    
    posts.update({"_id":postid}, {"$inc":{"flags":times}})
    users.update({"_id":userid}, {"$addToSet":{"flagged":postid}})
    
def unflag_post(userid, postid, timestamp=datetime.now().isoformat(), times=1):
    postid = ObjectId(postid)
    flagged = get_user_flags(userid)
    if postid not in flagged:
        raise ValueError("Cannot unflag before flag on postid " + str(postid))
    
    posts.update({"_id":postid}, {"$inc":{"flags":-times}})
    users.update({"_id":userid}, {"$pull":{"flagged":postid}})
    
def flag_comment(userid, commentid, timestamp=datetime.now().isoformat(), times=1):
    commentid = ObjectId(commentid)
    flagged = get_user_flags(userid)
    if commentid in flagged:
        raise ValueError("Double-vote detected on commentid " + str(commentid))
    
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.flags":times}})
    users.update({"_id":userid}, {"$addToSet":{"flagged":commentid}})
        
def unflag_comment(userid, commentid, timestamp=datetime.now().isoformat(), times=1):
    commentid = ObjectId(commentid)
    flagged = get_user_flags(userid)
    if commentid not in flagged:
        raise ValueError("Cannot unflag before flag on commentid " + str(commentid))
    
    posts.update({"comments._id":commentid}, {"$inc":{"comments.$.flags":-times}})
    users.update({"_id":userid}, {"$pull":{"flagged":commentid}})
##############################################################################
# End Real Time Server Methods                                               #
##############################################################################


#Make some data for the database:
def populate():
    print("Starting")
    clean_collections()
    
    cs1 = create_class("Columbia", "Alfred Aho", "Intro to CS", "1", "2012-05-11")
    print("Created classes")

    Anonymous = create_user("Anonymous", "", "admin", "Anonymous", None, "student")
    Mark = create_user("Mark", "Liu", "admin", "ml2877@columbia.edu", "Columbia", type="student")
    Amanda = create_user("Amanda", "Pickering", "test", "amanda@columbia.edu", "Columbia", type="admin")
    Ankit = create_user("Ankit", "Shah", "admin", "ankit@upenn.edu", "U. Penn", type="professor")
    print("Created users")
    
    register_user_for_class(Mark, cs1)
    register_user_for_class(Amanda, cs1)
    register_user_for_class(Ankit, cs1)

    print("Registered users for some classes")
    
    lecture1 = create_event_for_class(cs1, "Lecture", "Hamilton 207", datetime(2011, 9, 6, 13, 40).isoformat(), datetime(2011, 9, 6, 15).isoformat(), "The first lecture!")
    print("Created event for a class")
        
    print("Done")
 
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
            
#Test functionality when this file is run as a standalone program:
if __name__ == '__main__': populate()