from forms.forms import CreateEventForm
from env import env, BaseHandler, check_prof
from tornado.web import authenticated
import db.classes
import json
from datetime import date

class ViewCalendar(BaseHandler):
    template = env.get_template("calendar/calendar.template")
    @authenticated
    def get(self, class_id, month=None, year=None):
        if not (month and year):
            today = date.today()
            month = today.month
            year = today.year
        #Check if we are member of the class
        if db.classes.check_members(class_id, self.get_current_user()):
            form = CreateEventForm()
            # form.event_type.choices = {'Lecture':'Lecture'}
            self.write(self.template.render(class_id=class_id, form=form, month=month, year=year))
        else:
            self.write("You must be a member of this class!") #TODO: Make error pages for auth stuff...
#Details for some event
class CalendarDetails(BaseHandler):
    @authenticated
    def get(self, calendar_id):
        item = db.calendar.get_item(calendar_id)
        self.write(json.dumps(item, skipkeys=True, default=str))
#JSON Feed
class CalendarFeed(BaseHandler):
    @authenticated
    def get(self, class_id):
        if db.classes.check_members(class_id, self.get_current_user()):
            start = self.get_argument("start")
            end = self.get_argument("end")
            #The calendar program asks for 
            start = date.fromtimestamp(int(start))
            end = date.fromtimestamp(int(end))
            
            start_string = start.isoformat()[:16] #Lop off the seconds data
            end_string = end.isoformat()[:16]
            
            search_results = db.calendar.search_items(start_string, end_string)
            translated = list()
            #Search results is not in the proper format. Translate them
            for result in search_results:
                print(result)
                item = {'id':str(result['_id']), 
                        'title':result.get('title') or result['type'],  
                        'start':result['start'],
                        'end':result['finish'],
                        'url':'/calendar/details/' + str(result['_id']),
                        'className':result['type'],
                        'editable':False}
                translated.append(item)
                
            print(search_results)
            self.write(json.dumps(translated))
        else:
            self.write("") #Is it better to return 404?
    
class CreateCalendarStandalone(BaseHandler):
    @authenticated
    @check_prof
    def post(self, class_id):
        data = json.loads(self.get_argument("data"))
        start = data['start']
        finish = data['finish']
        type = data['type']
        details = data['details']
        attach_convo = data['attach_convo']
        day_offset = data.get('day_offset', 0)
        hour_offset = data.get('hour_offset', 0)
        #db.calendar.create_standalone(class_id, start, finish, type, details, attach_convo, day_offset, hour_offset)
        

class CreateCalendarSeries(BaseHandler):
    #Gimme some json data!
    @authenticated
    @check_prof
    def post(self, class_id):
        data = json.loads(self.get_argument("data"))
        start = data['start']
        finish = data['finish']
        type = data['type']
        details = data['details']
        times = data['times']
        attach_convo = data['attach_convo']
        day_offset = data.get('day_offset', 0)
        hour_offset = data.get('hour_offset', 0)
        db.calendar.create_series(class_id, start, finish, type, details, times, attach_convo, day_offset, hour_offset)
    