from env import env, BaseHandler, check_prof
from tornado.web import authenticated
import db.classes
import json
from datetime import date

class ViewCalendar(BaseHandler):
    template = env.get_template('calendar/view_calendar.template')
    @authenticated
    def get(self, class_id, month=None, year=None):
        if not (month and year):
            today = date.today()
            month = today.month
            year = today.year
        #Check if we are member of the class
        if db.classes.check_members(class_id, self.get_current_user()):
            # Display Calendar
            self.write(self.template.render(class_id=class_id))
        else:
            self.write("You must be a member of this class!") #TODO: Make error pages for auth stuff...
            
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
        db.calendar.create_standalone(class_id, start, finish, type, details, attach_convo, day_offset, hour_offset)
        

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
    