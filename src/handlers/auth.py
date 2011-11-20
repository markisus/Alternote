from env import BaseHandler, env, prof_code
from db.users import get_user
from db.logins import db_login
from forms.forms import LoginForm, RegistrationCodeForm
from tornado.web import authenticated
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
        form = LoginForm(**self.get_params())
        if form.validate():
            try:
                user = get_user(form.email.data)
            except KeyError:
                self.write("No username or wrong password")
                return
            if user['password'] == form.password.data:
                session = db_login(user['_id'])
                self.set_cookie('session', session)
                next = self.get_argument("next", "/")
                self.redirect(next)
                return
            else:
                self.write("No username or wrong password")
        self.write(self.template.render(form=form))
        
class LogoutHandler(BaseHandler):
    @authenticated
    def get(self):
        self.clear_cookie('userid')
        self.redirect("/")