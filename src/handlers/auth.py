from env import BaseHandler, env, prof_code
from db.logins import db_login, db_logout
from db.users import get_user
from forms.forms import LoginForm, RegistrationCodeForm
from tornado.web import authenticated
import hashlib
#Handlers related to authentication
        
class LoginHandler(BaseHandler):
    template = env.get_template('auth/login.template')

    def get(self):
        form = LoginForm()
        userid = self.get_current_user()
        if userid:
            self.write("Note: You are already logged in as " + userid)
        self.write(self.template.render(form=form))

    def post(self):
        form = LoginForm(formdata=self.get_params())
        if form.validate():
            try:
                user = get_user(form.email.data)
            except KeyError:
                self.write("No username or wrong password")
                return
            m = hashlib.sha256()
            m.update(form.password.data)
            if user['password'] == m.hexdigest():
                session = db_login(user['_id'])
                self.set_cookie('session', session)
                next = self.get_argument("next", self.reverse_url('ViewClasses'))
                self.redirect(next)
                return
            else:
                self.write("No username or wrong password")
        self.write(self.template.render(form=form))
        
class LogoutHandler(BaseHandler):
    @authenticated
    def get(self):
        session = self.get_cookie('session', None)
        db_logout(session)
        self.clear_cookie('session')
        self.redirect("/")