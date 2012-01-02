from db.collections import *
import hashlib

def get_user_display_info(userid, anon=False):
#    print("Getting user disiplay info, anon: " + str(anon))
    result = users.find_one({'_id':userid}, {'_id':1, 'first_name':1, 'last_name':1, 'type':1}) #TODO: Index type for covered query?
    if result == None:
        raise KeyError("No user with key " + str(userid) + " exists")
    if anon:
        anonymize(result)
    return result

def reset_password(user_id, old_password, new_password):
    m_old = hashlib.sha256()
    m_old.update(old_password)
    
    m_new = hashlib.sha256()
    m_new.update(new_password)
    
    #Check old password
    pw = users.find_one({'_id':user_id}, {'password':1})['password']
    
    if pw == m_old.hexdigest():
        users.update({'_id':user_id}, {'$set': {'password':m_new.hexdigest()}})
        return True
    else:
        return False
    
def anonymize(author):
    author['_id'] = "Anonymous"
    author['first_name'] = "Anonymous"
    author['last_name'] = "" 
    author['type'] = "student"
    return author

def create_user(first_name, last_name, password, email, school, type="student"):
    print("Inside create user!")
    m = hashlib.sha256()
    m.update(password)
    return users.insert(
                 {'_id':email,
                  'classes':[],
                  'flagged':[],
                  'voted':[],
                  'anonymous_items':[],
                  'first_name':first_name,
                  'last_name':last_name,
                  'email':email,
                  'school':school,
                  'password': m.hexdigest(),
                  'type':type,
                  }
                , safe=True)

def get_user(userid):
    result = users.find_one({'_id':userid})
    if result == None:
        raise KeyError("No user with key " + str(userid) + " exists")
    return result

def get_classes(userid):
    result = users.find_one({'_id':userid}, {'classes':1})
    return result['classes']

def set_avatar(user_id, file_name):
    avatars.update({"_id":user_id}, {"_id":user_id, "file_name":file_name}, upsert=True)

def get_avatar(user_id):
    avatar = avatars.find_one({"_id":user_id})
    if not avatar:
        raise KeyError("Avatar for " + user_id + " not found.")
    return avatar['file_name']
