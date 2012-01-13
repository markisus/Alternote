from datetime import datetime as dt, timedelta
from db.classes import *
from db.collections import *
import itertools

dt_format = "%Y-%m-%dT%H:%M"
d_format = "%Y-%m-%d"

#Get one
def get_item(event_id):
    event_id = ObjectId(event_id)
    return events.find_one({'_id':event_id})

#Delete item
def delete_item(event_id):
    event_id = ObjectId(event_id)
    files.update({"tags._id":event_id}, {"$pull":{"tags":{"_id":event_id}}})
    events.remove({"_id":event_id})
    posts.remove({'event_id':event_id})
    
#Get all
def get_all(class_id):
    result = list(events.find({'class._id':class_id}))
#    print(result)
    return result

#edit 
def edit_item(event_id, changes):
    print(changes)
    #Reset convo_start:
    convo_start = changes['start']
    if changes['dummy']:
        changes['hours_before'] = 0
        changes['days_before'] = 0
    else:
        try:
            listed_start = dt.strptime(changes['start'][:16], "%Y-%m-%dT%H:%M")
            delta = timedelta(hours=changes['hours_before'], days=changes['days_before'])
            convo_start = (listed_start - delta).isoformat()[:16] #Lop off the seconds data
            changes['convo_start'] = convo_start
        except ValueError:
            pass #Ignore parse error
    
    m_changes = {"$set":{i:changes[i] for i in changes.keys()}}
    
    print(m_changes)
    events.update({"_id":ObjectId(event_id)}, m_changes)
    
#Finds standlone items
def search_items(class_id, start, finish, convos_only=False, limit=None):
    query = {'$or':[
                            #S s f F - Complete Overlap within the search range
                            {'start':{'$gt':start},
                             'finish':{'$lt':finish},
                             'broadcast':False,
                             'class._id':class_id
                             },
                            #s S f - Intersects the start of the search range
                           {'start':{'$lt':start},
                            'finish':{'gt':start},
                            'broadcast':False,
                            'class._id':class_id
                            },
                            #s F f - Intersects the end of the search range
                           {'start':{'$lt':finish},
                            'finish':{'$gt':finish},
                            'broadcast':False,
                            'class._id':class_id
                            }
                           ]}
    #Only look for conversations
    if convos_only:
        for item in query['$or']:
            item['dummy'] = False
    
    if limit:
        result = events.find(query).sort('start', 1).limit(limit)
    else:
        result = events.find(query).sort('start', 1)
    return list(result)

#def create_standalone(class_id, title, start, finish, type, details, attach_convo=False, day_offset=0, hour_offset=0, series_id=None):
#    convo_id = None
#    if attach_convo:
#        startdt = dt.strptime(start[:16], dt_format)
#        tdelta = timedelta(days=day_offset, hours=hour_offset)
#        convo_start = (startdt - tdelta).isoformat()[:16]
#        convo_id = create_event_for_class(class_id, type, start=convo_start, details=details)
#        print("attached convo")
#    result = calendar.insert({
#                            'title':title,
#                            'start':start,
#                            'finish':finish,
#                            'type':type,
#                            'details':details,
#                            'cal_type':'standalone',
#                            'convo_id': convo_id,
#                            'series_id': series_id #This event might be one of a group of events
#                            })
#    return str(result)

#We might do up to 100 DB inserts... lots of room for improvement in this method
def create_series(class_id, title, start, finish, type, details, times, attach_convo=False, day_offset=0, hour_offset=0):
    MAX_SERIES = 100 #Limit the number of events in a series
    
#    sid = calendar.insert({
#                           'title':title,
#                           'start':start,
#                           'finish':finish,
#                           'type':type,
#                           'details':details,
#                           'cal_type':'series',
#                           'detached':[] #User might choose to detach certain items from the series
#                           })
    
    startdt = dt.strptime(start[:10], d_format)
    finishdt = dt.strptime(finish[:10], d_format)
    curr_day = startdt
    a_day = timedelta(days=1)
    counter = 0
    weekdays = ["m", "t", "w", "r", "f", "s", "u"]
    
    while(curr_day < finishdt and counter < MAX_SERIES):
        weekday = weekdays[curr_day.weekday()]
        if weekday in times.keys():
            curr_start = times[weekday][0]
            curr_finish = times[weekday][1]
            curr_day_string = curr_day.isoformat()[:10]
            #create_standalone(class_id, title, curr_day_string+"T"+curr_start, curr_day_string+"T"+curr_finish, type, details, attach_convo, day_offset, hour_offset, series_id=sid)
            create_event_for_class(class_id, "Lecture", "Lecture", curr_day_string+"T"+curr_start, curr_day_string+"T"+curr_finish, hour_offset, day_offset, dummy=(not attach_convo))
        curr_day = curr_day + a_day
        counter += 1
    