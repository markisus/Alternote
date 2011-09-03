from pymongo import Connection, ASCENDING, DESCENDING
from pymongo.errors import *
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

posts = alternote.events.posts
posts.ensure_index([('event',1),('votes',1)])

classes = alternote.classes
#End Binding collection names and setting indices

def clean_collections():
    users.remove()
    events.remove()
    posts.remove()
    classes.remove()


def create_class(university, instructor, name, section, finish_date, tags=[]):
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

def create_user(first_name, last_name, password, email, university, classes=[]):
    return users.insert(
                 {'_id':email,
                  'first_name':first_name,
                  'last_name':last_name,
                  'email':email,
                  'university':university,
                  'classes':classes,
                  'password':password
                  }
                 , safe = True
                )

def register_user_for_class(userid, classid):
    users.update( 
                 {'_id':userid}, 
                 {'$addToSet': 
                    {'classes':classid}
                }
            )

def create_event_for_class(classid, type, location, start_time, end_time, details):
    return events.insert(
                    {'type':type,
                     'class':classid,
                     'location':location,
                     'start_time':start_time,
                     'end_time':end_time,
                     'details':details
                    }
                  , safe = True
                  )

def __author_query(userid):
    return users.find(
                        {'_id':userid}, {'first_name':1, 'last_name':1},
                        limit=1
                    ).hint(
                           [('_id',1), ('first_name',1), ('last_name',1)]
                    )[0] #covered query

def create_post_for_event(eventid, userid, post):
    author = __author_query(userid)
    
    return posts.insert(
                 {'post':post,
                  'votes':0,
                  'event':eventid,
                  'author':author,
                  'comments':[],
                  }
                 )

def get_top_posts_for_event(eventid, post_limit=50):
    return posts.find({'event':eventid}, limit=post_limit).sort('votes', direction=DESCENDING).hint([('event',1),('votes',1)])

def get_other_posts_for_event(eventid, vote_cap, post_limit=50):
    return posts.find({'event':eventid, 'votes':{'$lte':vote_cap}}, limit=post_limit).sort('votes', direction=DESCENDING).hint([('event',1),('votes',1)])

def upvote_post(postid, times=1):
    posts.update({"_id":postid}, {"$inc":{"votes":times}})
    
def downvote_post(postid, times=1):
    posts.update({"_id":postid}, {"$inc":{"votes":-times}})
    
def create_comment_for_post(postid, userid, comment, retries=10):
    updatedExisting = False
    retry_counter = 0
    while (not updatedExisting) and retry_counter < retries:
        comment_id = str(time()) + str(randint(0, 9))
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
    
def upvote_comment(postid, commentid, times=1):
    posts.update({"_id":postid, "comments._id":commentid}, {"$inc":{"comments.$.votes":times}})
    
def downvote_comment(postid, commentid, times=1):
    posts.update({"_id":postid, "comments._id":commentid}, {"$inc":{"comments.$.votes":-times}})

#Make some data for the database:
def populate():
    print("Starting")
    clean_collections()
    
    cs1 = create_class("Columbia", "Alfred Aho", "Intro to CS", "1", "2012-05-11")
    cc1 = create_class("Columbia", "Jennifer Nash", "Columbia Core", "1", "2012-05-11")
    math1 = create_class("Columbia", "John Nash", "Mathematics", "1", "2012-05-11") 
    math2 = create_class("Columbia", "Leonard Euler", "Mathematics", "2", "2012-05-11")    
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
    
    lecture1 = create_event_for_class(cs1, "Lecture 1", "Hamilton 207", datetime(2011, 9, 6, 13, 40), datetime(2011, 9, 6, 15), "The first lecture!")
    print("Created event for a class")
    
    lecture1_posts = []
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
    
#Test functionality when this file is run as a standalone program:
if __name__ == '__main__': populate()