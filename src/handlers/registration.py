from env import BaseHandler, env, prof_code
from forms.forms import ProfRegistrationForm, RegistrationForm, AdminRegistrationForm
from db.schools import get_schools
from db.users import create_user
from db.logins import db_login
from db.codes import lookup_code
from db.classes import register_user_for_class, get_class
from pymongo.errors import DuplicateKeyError

class RegularRegistration(BaseHandler):
    #Not really student registration
    template = env.get_template('registration/student_registration.template')
    
    def get(self):
        print("Regular Registration")
        code = self.get_secure_cookie("code")
        try:
            code_data = lookup_code(code)
        except KeyError:
            self.write("Key does not exist")
            return
        code_type = code_data['type']
        #If code_type is admin we should display the admin form
        if code_type == "student":
            form = RegistrationForm()
        elif code_type == "admin":
            form = AdminRegistrationForm()
        else:
            raise ValueError("Invalid code type " + code_type)
        self.write(self.template.render(form=form))
        
    def post(self):
        code = self.get_secure_cookie("code")
        try:
            code_data = lookup_code(code)
        except KeyError:
            self.write("Key does not exist")
            return
        code_type = code_data['type']
        class_id = code_data['class_id']
        
        admin_form = False
        if code_type == "student":
            form = RegistrationForm(formdata=self.get_params())
        elif code_type == "admin":
            form = AdminRegistrationForm(formdata=self.get_params())
            admin_form = True
        else:
            raise ValueError("Invalid code type " + code_type)
        
        if form.validate():
            if admin_form:
                type = form.type.data
            else:
                type = "student"
            first_name = form.first_name.data
            last_name = form.last_name.data
            password = form.password.data
            email = form.email.data
            school = get_class(class_id)['school']
            try:
                user_id = create_user(first_name, last_name, password, email, school, type=type)
            except DuplicateKeyError:
                self.write("User with that email already exists")
                return
            register_user_for_class(user_id, class_id, type + "s") #Pluralize the category (this kind of sucks)
            session = db_login(user_id)
            self.set_cookie('session', session)
            self.redirect(self.reverse_url('ViewClasses'))
        else:
            self.write(self.template.render(form=form))        
            
class ProfessorRegistration(BaseHandler):
    template = env.get_template('registration/professor_registration.template')
    
    def prepare(self):
        schools = get_schools()
        self.school_choices = [(school['_id'], school['name']) for school in schools]
    def get(self):
        #Check registration code:
        code = self.get_secure_cookie("code")
        if code == prof_code:
            #Get a list of schools:
            form = ProfRegistrationForm()
            form.school.choices = self.school_choices
            self.write(self.template.render(form=form))
    def post(self):
        print(self.school_choices)
        form = ProfRegistrationForm(formdata=self.get_params())
        form.school.choices = self.school_choices
        if form.validate():
            school = form.school.data
            first_name = form.first_name.data
            last_name = form.last_name.data
            email = form.email.data
            password = form.password.data
            try:
                user_id = create_user(first_name, last_name, password, email, school, type="professor")
            except DuplicateKeyError:
                self.write("User with that email already exists")
                return
            session = db_login(user_id)
            self.set_cookie('session', session)
            self.write("Success!")
            self.redirect(self.reverse_url('CreateClass'))
        else:
            self.write(self.template.render(form=form))
            
