from db.collections import *
from time import time
from datetime import datetime
from db.users import get_user_display_info
import cgi

def record_anon_item(userid, objectid):
    print("\tanon: " + str(userid) + " " + str(objectid))
    objectid = ObjectId(objectid)
    users.update({'_id':userid}, {"$addToSet":{"anonymous_items":objectid}})
        
#Get the user object with only the info we need for display purposes
def is_anon_author(userid, objectid):
    objectid = ObjectId(objectid)
    result = users.find_one({"anonymous_items":objectid}, {"_id":1})
    if not result:
        return False
    return str(result['_id']) == userid

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
    result = events.posts.find_one({'_id':postid}, {'_id':0, 'event_id':1})
    if result != None:
        return result['event_id']

def get_eventid_of_comment(commentid):
    commentid = ObjectId(commentid)
    result = events.posts.find_one({'comments._id':commentid}, {'event_id':1})
    if result != None:
        return result['event_id']


#def create_post_for_event(userid, eventid, post, anonymous=False):
#    timestamp=datetime.now().isoformat()
#    author = get_user_display_info(userid, anon=anonymous)
#    result = posts.insert(
#                 {'message':post,
#                  'votes':0,
#                  'flags':0,
#                  'event':ObjectId(eventid),
#                  'author':author,
#                  'comments':[],
#                  'timestamp':timestamp,
#                  }
#                 )
#    if anonymous: 
#        record_anon_item(userid, result)
#    return str(result)
#Everything is a "message"
def create_message_for_event(userid, message, parent_id=None, eventid=None, anonymous=False):
    timestamp=datetime.now().isoformat()
    author = get_user_display_info(userid, anon=anonymous)
    #Make sure the parent belongs to the same event
    if parent_id:
        parent_id = ObjectId(parent_id)
        parent = posts.find_one({'_id':parent_id})
        if not parent:
            raise ValueError("Parent not found")
        else:
            eventid = parent['event_id']
    data = {'message':cgi.escape(message),
                  'votes':0,
                  'flags':0,
                  'event_id':ObjectId(eventid),
                  'author':author,
                  'parent_id':parent_id,
                  'timestamp':timestamp,
                  }
    id = posts.insert(data)
    data.update({'_id': id})
    if anonymous: 
        print("Recording anon item!")
        record_anon_item(userid, id)
    return data

#Now the function also gets comments...
def get_top_posts_for_event(eventid):
#    print("GETTING POSTS FOR " + str(eventid))
    eventid = ObjectId(eventid)
    return list(posts.find({'event_id':ObjectId(eventid)}).sort('timestamp', direction=ASCENDING).hint([('event',1),('timestamp',1)]))

def get_children_ids(objectid):
    objectid = ObjectId(objectid)
    return [p['_id'] for p in posts.find({'parent_id':objectid})]
#def create_comment_for_post(userid, postid, comment, anonymous=False):
#    timestamp=datetime.now().isoformat()
#    postid = ObjectId(postid)
#    comment_id = ObjectId()
#    author = get_user_display_info(userid, anonymous)
#    if anonymous: #Wipe identifying info
#        record_anon_item(userid, comment_id)
#        #Save this commentid into the user
#    comment = {
#                'message':comment,
#                'votes':0,
#                'flags':0,
#                'timestamp':timestamp,
#                'author':author,
#                '_id':comment_id
#               }
#        
#    posts.update({'_id':postid, 'comments._id':{'$ne':comment_id}},
#                  {'$push': {'comments':comment}},
#              )
#        
#    return str(comment_id) #Comment id unique within a post
def create_post_for_event(userid, eventid, post, anonymous=False):
    return create_message_for_event(userid, message=post, eventid=eventid, anonymous=anonymous)

def create_comment_for_post(userid, postid, comment, anonymous=False):
    return create_message_for_event(userid=userid, message=comment, parent_id=postid, anonymous=anonymous)

def delete_object(objectid):
    objectid = ObjectId(objectid)
    children = get_children_ids(objectid)
    removals = children + [objectid]
    posts.remove({"_id":{"$in":removals}});
    
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
#    vote_comment(userid, objectid)
    users.update({"_id":userid}, {"$addToSet":{"voted":objectid}})

def unvote_object(userid, objectid):
    objectid = ObjectId(objectid)
    voted = get_user_votes(userid)
    if objectid not in voted:
        raise ValueError("Cannot unupvote before upvote on object " + str(objectid))
    unvote_post(userid, objectid)
#    unvote_comment(userid, objectid)
    users.update({"_id":userid}, {"$pull":{"voted":objectid}})

def flag_object(userid, objectid):
    objectid = ObjectId(objectid)
    flagged = get_user_flags(userid)
    if objectid in flagged:
        raise ValueError("Double-flag detected on object " + str(objectid))    
    flag_post(userid, objectid)
#    flag_comment(userid, objectid)
    users.update({"_id":userid}, {"$addToSet":{"flagged":objectid}})

def unflag_object(userid, objectid):
    objectid = ObjectId(objectid)
    flagged = get_user_flags(userid)
    if objectid not in flagged:
        raise ValueError("Cannot unflag before flag on object " + str(objectid))
    unflag_post(userid, objectid)
#    unflag_comment(userid, objectid)
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