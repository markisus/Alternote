#The 'index' page: handles registration code redirects and logins
from forms.forms import RegistrationCodeForm, LoginForm, MailingListForm
from handlers.env import BaseHandler, prof_code, env
from db.users import get_user
from db.logins import db_login

class LandingPage(BaseHandler):
    template = env.get_template('landing_page.template')
    def get(self):
        #Display the landing page
        self.write(self.template.render(emailForm=MailingListForm(), regForm=RegistrationCodeForm(), loginForm=LoginForm()))
        
    def post(self):
        #Handle the registration code
        code = self.get_argument("code")
        self.set_secure_cookie("code", code, expires_days=1)
        if (code == prof_code):
            self.redirect(self.reverse_url('ProfessorRegistration'))
        else:
            self.redirect(self.reverse_url('RegularRegistration'))

class About(BaseHandler):
    template = env.get_template('pages/about.template')
    def get(self):
        navbar = self.render_navbar(None, False, True)
        self.write(self.template.render(navbar=navbar, loginForm=LoginForm()))
    
class Privacy(BaseHandler):
    template = env.get_template('pages/privacy.template')
    def get(self):
        navbar = self.render_navbar(None, False, True)
        self.write(self.template.render(navbar=navbar, loginForm=LoginForm()))

class Terms(BaseHandler):
    template = env.get_template('pages/terms.template')
    def get(self):
        navbar = self.render_navbar(None, False, True)
        self.write(self.template.render(navbar=navbar, loginForm=LoginForm()))
        
class Contact(BaseHandler):
    template = env.get_template('pages/contact.template')
    def get(self):
        navbar = self.render_navbar(None, False, True)
        self.write(self.template.render(navbar=navbar, loginForm=LoginForm()))