from pymongo import Connection, ASCENDING, DESCENDING
from pymongo.errors import *
from bson.objectid import ObjectId
from datetime import datetime
from random import randint
from time import time

default_connection = ('localhost', 27017)
connection = Connection(*default_connection)
alternote = connection.alternote

#Binding collection names and setting indices
users = alternote.users
users.ensure_index([('_id',1), ('first_name',1), ('last_name',1)]) #For covered queries

events = alternote.events
events.ensure_index([('class._id',1)])

posts = alternote.events.posts
posts.ensure_index([('event',1),('votes',1)])

classes = alternote.classes
posts.ensure_index([('_id',1), ('name',1)], [('university',1), ('tags',1)])

logins = alternote.logins
logins.ensure_index([('userid',1)])

#End Binding collection names and setting indices

def __author_query(userid):
    result = users.find(
                        {'_id':userid}, {'first_name':1, 'last_name':1},
                        limit=1
                    ).hint(
                           [('_id',1), ('first_name',1), ('last_name',1)]
                    )[0] #covered query
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

def create_user(first_name, last_name, password, email, university, classes=[], type="member"):
    return users.insert(
                 {'_id':email,
                  'first_name':first_name,
                  'last_name':last_name,
                  'email':email,
                  'university':university,
                  'classes':classes,
                  'password':password,
                  'type':type
                  }
                 , safe = True
                )
    
def get_user(userid):
    result = users.find_one({'_id':userid})
    if result == None:
        raise KeyError("No user with key " + str(userid) + " exists")
    return result


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

def create_event_for_class(classid, type, location, start_time, end_time, details):
    return events.insert(
                    {'type':type,
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

def get_event(eventid):
    eventid = ObjectId(eventid)
    result = events.find_one({'_id':eventid})
    if result == None:
        raise KeyError("No event with key " + str(eventid) + " exists")
    return result

def get_post(postid):
    postid = ObjectId(postid)
    result = events.find_one({'_id':postid})
    if result == None:
        raise KeyError("No post with key " + str(postid) + " exists")
    return result

def create_post_for_event(eventid, userid, post):
    author = __author_query(userid)
    
    return posts.insert(
                 {'post':post,
                  'votes':0,
                  'event':ObjectId(eventid),
                  'author':author,
                  'comments':[],
                  }
                 )

def get_top_posts_for_event(eventid, post_limit=50):
    eventid = ObjectId(eventid)
    return posts.find({'event':ObjectId(eventid)}, limit=post_limit).sort('votes', direction=DESCENDING).hint([('event',1),('votes',1)])

def get_other_posts_for_event(eventid, vote_cap, post_limit=50):
    return posts.find({'event':ObjectId(eventid), 'votes':{'$lte':vote_cap}}, limit=post_limit).sort('votes', direction=DESCENDING).hint([('event',1),('votes',1)])

def upvote_post(postid, userid=None, times=1): #Userid currently unused
    posts.update({"_id":ObjectId(postid)}, {"$inc":{"votes":times}})
    
def downvote_post(postid, userid=None, times=1): #Userid currently unused
    posts.update({"_id":ObjectId(postid)}, {"$inc":{"votes":-times}})

def __make_unique_string():
    return str(time()) + str(randint(0, 9)) #Since Tornado is single threaded, we prob dont need the random

def create_comment_for_post(postid, userid, comment, retries=10):
    postid = ObjectId(postid)
    updatedExisting = False
    retry_counter = 0
    while (not updatedExisting) and retry_counter < retries:
        comment_id = __make_unique_string()
        author = __author_query(userid)
        comment = {
                    'comment':comment,
                    'votes':0,
                    'author':author,
                    '_id':comment_id
                   }
        
        result = posts.update({'_id':postid, 'comments._id':{'$ne':comment_id}},
                      {'$push': {'comments':comment}},
                  safe=True)
        updatedExisting = result['updatedExisting']
        
    if not updatedExisting:
        raise IOError("Could not generate unique id for this comment, exceeded retries.")
    else:
        return comment_id #Comment id unique within a post
    
def upvote_comment(postid, commentid, userid=None, times=1):
    postid = ObjectId(postid)
    posts.update({"_id":ObjectId(postid), "comments._id":commentid}, {"$inc":{"comments.$.votes":times}})
    
def downvote_comment(postid, commentid, userid=None, times=1):
    postid = ObjectId(postid)
    posts.update({"_id":ObjectId(postid), "comments._id":commentid}, {"$inc":{"comments.$.votes":-times}})

def search_classes(university, tags, match="any"):
    """default match any tag, set match="all" to match all tags"""
    if match == "any":
        return classes.find({'university':university, 'tags':{'$in':tags}})
    if match == "all":
        return classes.find({'university':university, 'tags':{'$all':tags}})
    
    raise ValueError("Missing search option")

#Make some data for the database:
def populate():
    print("Starting")
    clean_collections()
    
    cs1 = create_class("Columbia", "Alfred Aho", "Intro to CS", "1", "2012-05-11")
    cc1 = create_class("Columbia", "Jennifer Nash", "Columbia Core", "1", "2012-05-11")
    math1 = create_class("Columbia", "John Nash", "Mathematics", "1", "2012-05-11") 
    math2 = create_class("Columbia", "Leonard Euler", "Humanities", "2", "2012-05-11")    
    huma1 = create_class("U. Penn", "John Smith", "Humanities", "1", "2011-12-25")
    econ1 = create_class("U. Penn", "Adam Smith", "Economics", "1", "2011-05-11")
    econ2 = create_class("U. Penn", "Alfred Keynes", "Economics", "2", "2012-05-11")
    econ3 = create_class("U. Penn", "Ludwig Von Mises", "Economics", "3", "2012-05-11")
    print("Created classes")

    Mark = create_user("Mark", "Liu", "admin", "ml2877@columbia.edu", "Columbia")
    Amanda = create_user("Amanda", "Pickering", "test", "amanda@columbia.edu", "Columbia")
    Ankit = create_user("Ankit", "Shah", "admin", "ankit@upenn.edu", "U. Penn")
    Tim = create_user("Tim", "Liu", "test", "timliu@upenn.edu", "U. Penn")
    print("Created users")
    
    register_user_for_class(Mark, cs1)
    register_user_for_class(Mark, cc1)
    register_user_for_class(Mark, math2)
    
    register_user_for_class(Amanda, math1)
    register_user_for_class(Amanda, cc1)
    
    register_user_for_class(Ankit, econ1)
    register_user_for_class(Ankit, huma1)
    register_user_for_class(Tim, econ1)
    register_user_for_class(Tim, econ2)
    register_user_for_class(Tim, econ3)
    print("Registered users for some classes")
    
    lecture1 = create_event_for_class(cs1, "Lecture", "Hamilton 207", datetime(2011, 9, 6, 13, 40), datetime(2011, 9, 6, 15), "The first lecture!")
    print("Created event for a class")
    
    for i in range(1000):
        post = create_post_for_event(lecture1, Mark, "I'm so excited for this new class! %d" % i)
        comment = create_comment_for_post(post, Amanda, "Lol I'm commenting on everything!")
        upvote_comment(post, comment, 1)
        upvote_comment(post, comment, 1)
        downvote_comment(post, comment, 1)
        upvote_post(post, i)
    print("Created posts for an event")
    
    for post in get_top_posts_for_event(lecture1):
        print(post)
        
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