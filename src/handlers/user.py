from env import BaseHandler, env, check_prof, ClassViewHandler
from tornado.web import authenticated
from constants import static_path

#Handlers related to user account stuff

class AccountPage(BaseHandler):
    @authenticated
    def get(self):
        self.write("This is the account page for " + self.get_current_user())