from db.collections import *
from datetime import datetime as dt
from datetime import timedelta
from db.users import get_user_display_info

def __class_query(classid):
    classdoc = classes.find({'_id':classid}, {'name':1, '_id':1}, limit=1).hint([('_id',1), ('name',1)])[0]
    if classdoc == None:
        raise KeyError("Registration failed; could not find class with key " + classid)
    return classdoc

def create_class(school, instructor_id, name, section, code, start_date, finish_date, alternate_codes=[], meet_times={}):
    result = classes.insert(
                   {'_id':'-'.join((school,name,section)),
                    'school':school, 
                    'code':code,
                    'alternate_codes':alternate_codes,
                    'name':name,
                    'section':section,
                    'start':start_date,
                    'finish':finish_date,
                    'instructors':[],
                    'tas':[],
                    'students':[],
                    'meet_times':meet_times,
                    }
                   , safe = True
                   )
    register_user_for_class(instructor_id, result, category="instructors")
    return result

def get_class(classid):
    result = classes.find_one({'_id':classid})
    if result == None:
        raise KeyError("No class with key " + str(classid) + " exists")
    return result

    
def register_user_for_class(user_id, class_id, category="students"):
    classdoc = classes.find({'_id':class_id}, {'name':1, '_id':0}, limit=1).hint([('_id',1), ('name',1)])[0]
    if classdoc == None:
        raise KeyError("Registration failed; could not find class with key " + class_id)
    
    class_name = classdoc['name']
    users.update( 
                 {'_id':user_id}, 
                 {'$addToSet': 
                    {'classes':__class_query(class_id)}
                }
            )
    user_doc = get_user_display_info(user_id)
    classes.update(
                  {'_id':class_id},
                  {'$addToSet':
                   {category:user_doc}
                  }
            )
    
def create_broadcast_for_class(class_id):
    create_event_for_class(class_id, "Broadcast", "Broadcast", broadcast=True)
    
def create_event_for_class(class_id, type, title, start="0", finish="9", hours_before=0, days_before=0, details="", dummy=False, broadcast=False):
    #We want to differentiate between the "real" start time and the listed start time
    if broadcast and dummy:
        print("Warning: Marking Broadcast as dummy")
    
    convo_start = start 
    try:
        listed_start = dt.strptime(start[:16], "%Y-%m-%dT%H:%M")
        delta = timedelta(hours=hours_before, days=days_before)
        convo_start = (listed_start - delta).isoformat()[:16] #Lop off the seconds data
    except ValueError:
        pass #Ignore parse error
    
    return events.insert(
                    {'type':type,
                     'title':title,
                     'class':__class_query(class_id), #Should this be changed to just class_id?
                     'convo_start':convo_start,
                     'start':start,
                     'finish':finish,
                     'details':details,
                     'dummy':dummy, #Dummy decides if the event is visible in the convos
                     'broadcast':broadcast
                    }
                  , safe = True
                  )
    
def check_instructor_and_tas(class_id, user_id):
    course = classes.find_one({"_id":class_id})
    if not course:
        raise KeyError("Course with id " + str(class_id) + " does not exist.")
    if user_id in __unpack_userids(course['instructors']) + __unpack_userids(course['tas']):
        return True
    else:
        return False
    
def check_members(class_id, user_id):
    course = classes.find_one({"_id":class_id})
    if not course:
        raise KeyError("Course with id " + str(class_id) + " does not exist.")
    if user_id in __unpack_userids(course['instructors']) + __unpack_userids(course['tas']) + __unpack_userids(course['students']):
        return True
    else:
        return False    
    
#List of userdocs
def __unpack_userids(docs):  
    return [doc['_id'] for doc in docs]
unpack_userids = __unpack_userids

def get_events_for_class(class_id):
    return events.find({'class._id':class_id})
