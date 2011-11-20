from collections import *

def db_login(userid):
    session = str(ObjectId())
    logins.insert({'_id':session, 'userid':userid})
    return session

def db_logout(session):
    logins.remove({'_id':session})

def db_get_userid(session):
    user = logins.find_one({'_id':session})
    if not user:
        raise KeyError("No user matching this session " + session)
    return user['userid']