from forms.forms import CreateEventForm
import db.conversations
from env import env, BaseHandler, check_prof, ClassViewHandler
from tornado.web import authenticated
import db.classes
import json
import datetime
from datetime import date

#Time formatter
def time_format(time_string):
    time_string = time_string[11:]
    hour = int(time_string[0:2])
    if hour > 11:
        if (hour == 12):
            time_string = str(hour) + time_string[2:] + "p"
        else:
            time_string = str(hour - 12) + time_string[2:] + "p"
    else:
        time_string += "a"
    return time_string

def twelve_hour_time(hour_string):
    hour, min = hour_string.split(":")
    hour = int(hour)
    hour = int(hour_string[:2])
    if hour > 12:
        hour_string = str(hour - 12) + ":" + min + "p"
    else:
        hour_string = str(hour) + ":" + min + "a"
    return hour_string

class ViewCalendar(ClassViewHandler):
    template = env.get_template("calendar/calendar.template")
    def render_get(self, class_id, month=None, year=None):
        if not (month and year):
            today = date.today()
            month = today.month
            year = today.year
            form = CreateEventForm()
            # Grab upcoming events
            start = "0"
            finish = "9"
            now = datetime.datetime.now().isoformat()[:16]
            upcoming = db.calendar.search_items(class_id, now, finish)
            return self.template.render(class_id=class_id, user_type=self.user_type, upcoming=upcoming, form=form, month=month, year=year)

    def render_post(self, class_id):
        print("POST CALLED!!!")
        if not (self.user_type in ['professor', 'ta']):
            raise ValueError("Insufficient Priveleges")
            
        form = CreateEventForm(formdata=self.get_params())
        if form.validate():
            name = form.name.data
            start_time = form.start_time.data
            finish_time = form.finish_time.data
            #all_day = form.all_day.data TODO
            day_offset = form.day_offset.data
            hour_offset = form.hour_offset.data
            attach_conversation = form.attach_conversation.data
            event_type = form.event_type.data
            #files = form.files.data TODO
            
            db.classes.create_event_for_class(class_id, event_type, name, start_time, finish_time, hour_offset, day_offset, dummy=(not attach_conversation))
        else:
            print("Validation failed" + str(form.errors))
        return "OK"
            
#Details for some event
class CalendarDetails(BaseHandler):
    @authenticated
    def get(self, class_id, calendar_id):
        item = db.calendar.get_item(calendar_id)
        self.write(json.dumps(item, skipkeys=True, default=str))
        
#JSON Feed
class CalendarFeed(BaseHandler):
    @authenticated
    def get(self, class_id):
        print("INSIDE CALENDARFEED")
        if db.classes.check_members(class_id, self.get_current_user()):
            start = self.get_argument("start")
            end = self.get_argument("end")
            #The calendar program asks for 
            start = date.fromtimestamp(int(start))
            end = date.fromtimestamp(int(end))
            
            start_string = start.isoformat()[:16] #Lop off the seconds data
            end_string = end.isoformat()[:16]
            
            search_results = db.calendar.search_items(class_id, start_string, end_string)
            translated = list()
            #Search results is not in the proper format. Translate them
            for result in search_results:
                title_time = time_format(result['start'][:16])
                result_title = result.get('title') or result['type']
                result_title = title_time + " " + result_title
                item = {'id':str(result['_id']), 
                        'title':result_title,  
                        'start':result['start'],
                        'end':result['finish'],
                        'url':self.reverse_url("CalendarDetails", class_id, str(result['_id'])),
                        'className':result['type'],
                        'editable':False}
                translated.append(item)
            print("DUMPING " + str(translated))
            self.write(json.dumps(translated))
        else:
            self.write("") #Is it better to return 404?
    
class CreateCalendarStandalone(BaseHandler):
    @authenticated
    @check_prof
    def post(self, class_id):
        print("CREATE STANDALONE")
        print(self.get_params())
        data = self.get_params()
        title = data['title'][0]
        start = data['start'][0]
        finish = data['end'][0]
        type = data['type'][0]
        attach_convo = data['auto_convo'][0]
        day_offset = data.get('day_offset', [0])[0]
        hour_offset = data.get('hour_offset', [0])[0]
        db.classes.create_event_for_class(class_id, type, title, start, finish, hour_offset, day_offset, dummy=not attach_convo)
        self.write("OK")

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
    