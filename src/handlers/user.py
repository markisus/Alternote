from env import BaseHandler, env
from tornado.web import authenticated
from constants import static_path
import db.users
import os
import tornado

#Handlers related to user account stuff
def get_avatar_url(user_id):
    try:
        file_name = db.users.get_avatar(user_id)
    except KeyError:
        file_name = "default-icon.png"
    return "/static/avatars/" + file_name

class GetAvatar(BaseHandler):
    def get(self, user_id, random_string=None):
        self.set_status(303)
        self.redirect(get_avatar_url(user_id))
        

class AccountPage(BaseHandler):
    template = env.get_template("user/account.template")
    
    @authenticated
    def get(self):
        user_id = self.get_current_user()
        user_info = db.users.get_user_display_info(user_id)
        self.render_out(user_id=user_id, user_info=user_info)
        
class ChangePassword(BaseHandler):      
    @authenticated
    def post(self):
        old_pass = self.get_argument("old_pass") 
        new_pass = self.get_argument("new_pass")
        if db.users.reset_password(self.get_current_user(), old_pass, new_pass):
            return
        else:
            raise tornado.web.HTTPError(401)
       
class AvatarUpload(BaseHandler):  
    def save_file_normal(self):
        print("saving normal file")
        name = self.request.files['qqfile']
        self.write("{error:'error'}")
        return
    
    def write_file_to_disk(self, file_name, contents):
        print("saving file to disk")
        extension = file_name.split(".")[-1]
        if not extension in ["jpg", "png", "gif", "bmp"]:
            raise ValueError(extension + " not allowed as an avatar")
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