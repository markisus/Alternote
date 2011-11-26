from datetime import datetime as dt, timedelta
from db.classes import *
from db.collections import *

dt_format = "%Y-%m-%dT%H:%M"
d_format = "%Y-%m-%d"

#Get one
def get_item(event_id):
    event_id = ObjectId(event_id)
    return events.find_one({'_id':event_id})
#Get all
def get_all(class_id):
    return list(events.find({'class_id':class_id}))

#Finds standlone items
def search_items(start, finish):
    print("inside seach_items with " + start + " " + finish)
    result = events.find({'$or':[
                            #S s f F - Complete Overlap within the search range
                            {'start':{'$gt':start},
                             'finish':{'$lt':finish},
                             'broadcast':False
                             },
                            #s S f - Intersects the start of the search range
                           {'start':{'$lt':start},
                            'finish':{'gt':start},
                            'broadcast':False,
                            },
                            #s F f - Intersects the end of the search range
                           {'start':{'$lt':finish},
                            'finish':{'$gt':finish},
                            'broadcast':False
                            }
                           ]}
                           )
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
    