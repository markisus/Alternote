from src.db.collections import *

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
                    'start_date':start_date,
                    'finish_date':finish_date,
                    'instructors':[instructor_id],
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
    classes.update(
                  {'id':class_id},
                  {'$addToSet':
                   {category:user_id}
                  }
            )
    

def create_event_for_class(class_id, type, start="0", end="9", details=""):
    return events.insert(
                    {'type':type,
                     'class':__class_query(class_id),
                     'start':start,
                     'end':end,
                     'details':details
                    }
                  , safe = True
                  )
    
def check_instructor_and_tas(class_id, user_id):
    course = classes.find_one({"_id":class_id})
    if not course:
        raise KeyError("Course with id " + str(class_id) + " does not exist.")
    if user_id in course['instructors'] + course['tas']:
        return True
    else:
        return False
    
def check_members(class_id, user_id):
    course = classes.find_one({"_id":class_id})
    if not course:
        raise KeyError("Course with id " + str(class_id) + " does not exist.")
    if user_id in course['instructors'] + course['tas'] + course['students']:
        return True
    else:
        return False    
                            
def get_events_for_class(class_id):
    return events.find({'class._id':class_id})