from src.db.collections import *

def create_user(first_name, last_name, password, email, school, type="student"):
    print("Inside create user!")
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
                  'password':password,
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
