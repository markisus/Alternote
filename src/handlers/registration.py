from env import BaseHandler, env, prof_code
from forms.forms import ProfRegistrationForm
from db.schools import get_schools
from db.users import create_user
from db.logins import db_login
from db.codes import lookup_code

from pymongo.errors import DuplicateKeyError

class StudentRegistration(BaseHandler):
    #template = env.get_template('registration/student_registration.template')
    
    def get(self):
        code = self.get_secure_cookie("code")
        code_data = lookup_code(code)
        
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
        form = ProfRegistrationForm(**self.get_params())
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
            
