#The 'index' page: handles registration code redirects and logins
from forms.forms import RegistrationCodeForm, LoginForm
from handlers.env import BaseHandler, prof_code, env
from db.users import get_user
from db.logins import db_login

class LandingPage(BaseHandler):
    template = env.get_template('landing_page.template')
    def get(self):
        #Display the landing page
        self.write(self.template.render(regForm=RegistrationCodeForm(), loginForm=LoginForm()))
        
    def post(self):
        #Handle the registration code
        code = self.get_argument("code")
        if (code == prof_code):
            self.set_secure_cookie("code", code, expires_days=1)
            self.redirect(self.reverse_url('ProfessorRegistration'))
        else:
            pass #Try student signup

class About(BaseHandler):
    template = env.get_template('pages/about.template')
    def get(self):
        self.write(self.template.render())
    
class Privacy(BaseHandler):
    template = env.get_template('pages/privacy.template')
    def get(self):
        self.write(self.template.render())

class Terms(BaseHandler):
    template = env.get_template('pages/terms.template')
    def get(self):
        self.write(self.template.render())
        
class Contact(BaseHandler):
    template = env.get_template('pages/contact.template')
    def get(self):
        self.write(self.template.render())