from env import BaseHandler, env, check_prof, ClassViewHandler
from tornado.web import authenticated
from constants import static_path
import db.users
import os
#Handlers related to user account stuff

class AccountPage(BaseHandler):
    template = env.get_template("user/account.template")
    
    @authenticated
    def get(self):
        self.render_out(user_id=self.get_current_user())
        
class AvatarUpload(BaseHandler):  
    def save_file_normal(self):
        print("saving normal file")
        name = self.request.files['qqfile']
        self.write("{error:'error'}")
        return
    
    def write_file_to_disk(self, file_name, contents):
        print("saving file to disk")
        extension = file_name.split(".")[-1]
        file_name = self.get_current_user() + "." + extension
        upload_path = os.path.join(static_path, "avatars")
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file_path = os.path.join(upload_path, file_name)
        file = open(file_path, 'wb')
        file.write(contents)
        db.users.set_avatar(self.get_current_user(), file_name)
        
    def save_file_xhr(self):
        print("Saving file xhr")
        body = self.request.body
        name = self.get_argument('qqfile')
        self.write_file_to_disk(name, body)
        print("writing ok")
        self.write("{success:'ok'}")
        self.finish()
        
    def post(self):
        print("File Upload...")
        if (self.get_argument("qqfile", False)):
            #XHR uploading
            print("XHRUploading")
            self.save_file_xhr()
        else:
            print("Regular uploading")
            self.save_file_normal() #Broken