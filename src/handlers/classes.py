from env import BaseHandler, env, check_prof
from forms.forms import CreateClassForm
from tornado.web import authenticated
import db.classes
import db.codes
import db.calendar

class CreateClass(BaseHandler):
    template = env.get_template("classes/create_class.template")

    @authenticated
    @check_prof
    def get(self):
        self.write(self.template.render(form=CreateClassForm()))
    
    @authenticated
    @check_prof
    def post(self):
        #The user is set by the professor checker
        user = self.user
        form = CreateClassForm(formdata=self.get_params())
        #return
        if form.validate():
            name = form.name.data
            section = form.section.data
            code = form.code.data
            alternate_codes = []
            if form.alternate_codes.data:
                alternate_codes = [c.strip() for c in form.alternate_codes.data.split(",") if c.strip()]
            start = form.start_date.data.isoformat()[:10]
            finish = form.finish_date.data.isoformat()[:10]
            days = ["m", "t", "w", "r", "f", "s", "u"]
            meet_times = dict()
            #Some magic to parse meet times
            for day in days:
                field = getattr(form, day)
                field_end = getattr(form, day + "_end")
                assert (field.data and field_end.data) or not (field.data and field_end.data), "Both must be filled or blank"
                assert field.data <= field_end.data, "Start time must be < end time"
                if field.data and field_end.data:
                    meet_times[day] = [field.data, field_end.data]
            school = user['school']
            class_id = db.classes.create_class(school, user['_id'], name, section, code, start, finish, alternate_codes, meet_times)
            #create the codes for this class
            db.codes.create_student_code(class_id)
            db.codes.create_ta_code(class_id)
            
            auto_convo = form.auto_convo.data
            day_offset = form.day_offset.data or 0
            hour_offset = form.hour_offset.data or 0
            
            db.calendar.create_series(class_id, name + " Lecture", start, finish, "Lecture", "", meet_times, auto_convo, day_offset, hour_offset)
            db.classes.create_broadcast_for_class(class_id)
            #Redirect to view classes
            self.redirect(self.reverse_url("ViewClasses"))
        else:
            print("Validation failed" + str(form.errors))
            self.write(self.template.render(form=form))
        
class ViewClasses(BaseHandler):
    template = env.get_template("classes/view_classes.template")
    
    @authenticated
    def get(self):
        classes = db.users.get_classes(self.get_current_user())
        self.write(self.template.render(classes=classes, reverse_url=self.reverse_url))
    
class ViewCodes(BaseHandler):
    @authenticated
    @check_prof
    def get(self, class_id):
        #Check class match
        try:
            if db.classes.check_instructor_and_tas(class_id, self.get_current_user()):
                codes = db.codes.lookup_codes(class_id)
                self.write("Everything checks out")
                for code in codes:
                    self.write("<br/>" + code['type'] + " code: " + code['_id'])
            else:
                self.write("You're not allowed to view this page!")
        except KeyError as e:
            self.write("I don't think this class exists. " + e.message)

            
                