from db.collections import *
from datetime import datetime as dt
from db.calendar import d_format

from pymongo.objectid import ObjectId
#Keep Track of File Metadata

def create_record(class_id, file_name, file_type):
    return files.insert({'class_id':class_id,
                  'name':file_name,
                  'tags': [],
                  'file_type':file_type,
                  })
    
def get_record(record_id):
    result = files.find_one({'_id':ObjectId(record_id)})
    if not result:
        raise KeyError("File record with id " + str(record_id) + " not found")
    return result

def get_class_id_for_record(record_id):
    result = files.find_one({'_id':ObjectId(record_id)}, {'_id':0, 'class_id':1})
    if not result:
        raise KeyError("File record with id " + str(record_id) + " not found")
    return result['class_id']
    

def check_record(class_id, file_name):   
    result = files.find_one({'class_id':class_id, 'name':file_name})
    return not (result is None)

def set_tags(record_id, event_ids):
    event_ids = [ObjectId(event_id) for event_id in event_ids]
    files.update({"_id":ObjectId(record_id)}, 
                 {"$set":{"tags":event_ids}})
    
def add_tags(record_id, event_ids):
    tags = __generate_tags(event_ids)
    files.update({'_id':ObjectId(record_id)},
                 {'$addToSet':{'tags':{'$each':tags}}}
                 )
    
def remove_tags(record_id, event_ids):
    event_ids = [ObjectId(event_id) for event_id in event_ids]
    files.update({'_id':ObjectId(record_id)},
                  {'$pull':
                    {'tags':{'$in':event_ids}}
                   }
                  )

def get_records(class_id):
    return list(files.find({'class_id':class_id}))

def remove_record(record_id):
    files.remove({'_id':ObjectId(record_id)})
    
def __generate_tags(event_ids):
    #Wrap event ids for Mongo $or query
    event_ids = [{'_id':ObjectId(event_id)} for event_id in event_ids]
#    results = events.find({'$or':event_ids})
#    tags = [ {'_id':result['_id'], 'title':result['title'], 'start':result['start'], 'type':result['type']} for result in results ]
#    return tags
    return event_ids

def get_files_for_event(event_id):
#    return list(files.find({'tags._id':ObjectId(event_id)}))
    return list(files.find({'tags':ObjectId(event_id)}))

def get_untagged(record_id):
    record = get_record(record_id)
    tagged_ids = record['tags']
    class_id = record['class_id']
    return list(events.find({'class._id':class_id, '_id':{'$nin':tagged_ids}, 'broadcast':False}))
    


    
    
    