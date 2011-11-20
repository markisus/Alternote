#The 'index' page: handles registration code redirects
from forms.forms import RegistrationCodeForm
from handlers.env import BaseHandler, prof_code, env
class LandingPage(BaseHandler):
    template = env.get_template('landing_page.template')
    def get(self):
        #Display the landing page
        self.write(self.template.render(form=RegistrationCodeForm()))
        
    def post(self):
        #Handle the registration code
        code = self.get_argument("code")
        if (code == prof_code):
            self.set_secure_cookie("code", code, expires_days=1)
            self.redirect(self.reverse_url('ProfessorRegistration'))
        else:
            pass #Try student signup