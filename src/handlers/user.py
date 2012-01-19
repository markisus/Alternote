from constants import static_path
from env import BaseHandler, env
from forms import forms
from tornado.web import authenticated
import db.users
import os
import tornado

#Handlers related to user account stuff
def get_avatar_url(user_id):
    try:
        file_name = "/static/avatars/" + db.users.get_avatar(user_id)
    except KeyError:
        file_name = "http://static1.robohash.com/" + user_id
        # file_name = "default-icon.png"
    return file_name

class GetAvatar(BaseHandler):
    def get(self, user_id, random_string=None):
        self.set_status(303)
        self.set_header("Cache-Control", "no-cache")
        self.redirect(get_avatar_url(user_id))
        
class AddClassPage(BaseHandler):
    template = env.get_template("user/add_class.template")
    
    @authenticated
    def get(self):
        self.render_out()
    
    def post(self):
        user_id = self.get_current_user()
        code = self.get_argument("code")
        code_doc = db.codes.lookup_code(code)
        class_id = code_doc['class_id']
        user_type = code_doc['type']
        if user_type == "student":
            db.classes.register_user_for_class(user_id, class_id, "students")
            self.redirect(self.reverse_url("ViewClasses"))
        elif user_type == "admin":
            self.set_secure_cookie("code", code)
            self.redirect(self.reverse_url("PrivelegedAddClassPage"))
        else:
            self.write("Error: code has no type")
            
class PrivelegedAddClassPage(BaseHandler):
    template = env.get_template("user/priveleged_add_class.template")
    
    @authenticated
    def get(self):
        #Check if the user is allowed to be on this page
        code = self.get_secure_cookie("code")
        code_doc = db.codes.lookup_code(code)
        class_id = code_doc['class_id']
        user_type = code_doc['type']
        if user_type != "admin":
            self.write("Something went wrong, code type must be admin to be on this page")
            return
        else:
            self.render_out()
    
    def post(self):
        #Check if the user is allowed to be on this page
        code = self.get_secure_cookie("code")
        code_doc = db.codes.lookup_code(code)
        class_id = code_doc['class_id']
        user_type = code_doc['type']
        if user_type != "admin":
            self.write("Something went wrong, code type must be admin to be on this page")
            return
        else:
            prof_or_ta = self.get_argument("prof_or_ta")
            db.classes.register_user_for_class(self.get_current_user(), class_id, prof_or_ta)
            self.redirect(self.reverse_url("ViewClasses"))
class AccountPage(BaseHandler):
    template = env.get_template("user/account.template")
    
    @authenticated
    def get(self):
        user_id = self.get_current_user()
        user_info = db.users.get_user_display_info(user_id)
        form = forms.ChangePasswordForm()
        self.render_out(user_id=user_id, user_info=user_info, form=form,)
        
    @authenticated
    def post(self):
        form = forms.ChangePasswordForm(formdata=self.get_params())
        user_id = self.get_current_user()
        user_info = db.users.get_user_display_info(user_id)
        if form.validate():
            old_pass = self.get_argument("old_pass") 
            new_pass = self.get_argument("new_pass")
            if db.users.reset_password(self.get_current_user(), old_pass, new_pass):
                self.render_out(user_id=user_id, user_info=user_info, form=form, message="Success!")
                return
            else:
                form.old_pass.errors.append("Old password incorrect")
        self.render_out(user_id=user_id, user_info=user_info, form=form,)

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