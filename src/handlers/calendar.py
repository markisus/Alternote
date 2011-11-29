from forms.forms import CreateEventForm
from env import env, BaseHandler, check_prof
from tornado.web import authenticated
import db.classes
import json
import datetime
from datetime import date

#Time formatter
def time_format(time_string):
    time_string = time_string[11:]
    if int(time_string[0:2]) > 12:
        time_string = str(int(time_string[0:2]) - 12) + time_string[2:] + "p"
    else:
        time_string += "a"
    return time_string

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
            # Check if we are professor of the class
            priveledged = db.classes.check_instructor_and_tas(class_id, self.get_current_user())
            # Grab upcoming events
            start = "0"
            finish = "9"
            now = datetime.datetime.now().isoformat()[:16]
            upcoming = db.calendar.search_items(class_id, now, finish, limit=10)
            # Render ui elements
            navbar = self.render_navbar(class_id, priveledged)
            sidebar = self.render_sidebar(class_id)
            self.write(self.template.render(class_id=class_id, form=form, month=month, year=year, sidebar=sidebar, navbar=navbar, upcoming=upcoming))
        else:
            self.write("You must be a member of this class!") #TODO: Make error pages for auth stuff...
    
    @authenticated
    @check_prof
    def post(self, class_id):
        form = CreateEventForm(formdata=self.get_params())
        if form.validate():
            name = form.name.data
            start_time = form.start_time.data
            finish_time = form.finish_time.data
            all_day = form.all_day.data
            day_offset = form.day_offset.data
            hour_offset = form.hour_offset.data
            attach_conversation = form.attach_conversation.data
            event_type = form.event_type.data
            files = form.files.data
            #TODO: Call the create_standalone method in db.calendar
            db.calendar.create_standalone(class_id, name, start_time, finish_time, event_type, details, attach_conversation, day_offset, hour_offset)
        else:
            print("Validation failed" + str(form.errors))
        self.write(self.template.render(class_id=class_id, form=form, month=month, year=year, sidebar=sidebar, navbar=navbar, upcoming=upcoming))
            
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
                        'url':'/calendar/details/' + str(result['_id']),
                        'className':result['type'],
                        'editable':False}
                translated.append(item)
                
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
    