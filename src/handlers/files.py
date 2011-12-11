from env import BaseHandler, env, check_prof, ClassViewHandler
from tornado.web import authenticated
from constants import static_path
import os
from forms.forms import FileForm
import db.classes
import db.files
import urllib
#File Uploading/Management


class Files(ClassViewHandler):
    template = env.get_or_select_template("files/edit_files.template")

    def render_get(self, class_id):
            files = db.files.get_records(class_id)
            sorted_files = sorted(files, cmp=lambda x,y: cmp(x['name'], y['name'])) #Lexicographic sort
            return self.template.render(form=FileForm(), files=sorted_files)

       
    def render_post(self, class_id):
        if not self.user_type in ['professor', 'ta']:
            raise ValueError("You need to be a prof or a ta")
        found = True
        try:
            f = self.request.files['file'][0]
        except KeyError as e:
            found = False
            print(e.message)
            
        if found:
            name = f['filename']
            type = f['content_type']
            body = f['body']
            
            #Check if file exists in database
            if db.files.check_record(class_id, name):
                self.write("A file with this name already exists!")
                return
            else:
                upload_path = os.path.join(static_path, "files", class_id)
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                print(upload_path)
                file_path = os.path.join(upload_path, name)
                file = open(file_path, 'wb')
                file.write(body)
                #Add meta data to the database
                db.files.create_record(class_id, name, type)
                #Everything Okay?
                print(self.reverse_url("Files", class_id))
                self.redirect(self.reverse_url("Files", urllib.quote(class_id)))
        else:
            self.write("Did you forget to choose a file?")
            
class FileUpload(BaseHandler):  
    def save_file_normal(self, class_id):
        name = self.request.files['qqfile']
        print(name)
        self.write("{error:'error'}")
        return
        #Check if file exists in database
#        if db.files.check_record(class_id, name):
#            self.write("A file with this name already exists!")
#            return
#        else:
#            upload_path = os.path.join(static_path, "files", class_id)
#            if not os.path.exists(upload_path):
#                os.makedirs(upload_path)
#            print(upload_path)
#            file_path = os.path.join(upload_path, name)
#            file = open(file_path, 'wb')
#            file.write(body)
#            #Add meta data to the database
#            db.files.create_record(class_id, name, type)
#            #Everything Okay?
#            print(self.reverse_url("Files", class_id))
#            self.redirect(self.reverse_url("Files", urllib.quote(class_id))) 

    def write_file_to_disk(self, class_id, file_name, contents):
        if db.files.check_record(class_id, file_name):
            self.write("{error:'file name collision'}")
            self.finish()
            return
        upload_path = os.path.join(static_path, "files", class_id)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        print(upload_path)
        file_path = os.path.join(upload_path, file_name)
        file = open(file_path, 'wb')
        file.write(contents)
        #Add meta data to the database
        db.files.create_record(class_id, file_name, file_name.split(".")[-1])
        
    def save_file_xhr(self, class_id):
        body = self.request.body
        name = self.get_argument('qqfile')
        self.write_file_to_disk(class_id, name, body)
        self.write("{success:'ok'}")
        self.finish()
        
    def post(self, class_id):
        print("File Upload...")
        print(self.request)
        if (self.get_argument("qqfile", False)):
            #XHR uploading
            print("XHRUploading")
            self.save_file_xhr(class_id)
        else:
            print("Regular uploading")
            self.save_file_normal(class_id)
            
class FileDelete(BaseHandler):           
    @authenticated
    @check_prof            
    def post(self, class_id):
        print("DELETE")
        if db.classes.check_instructor_and_tas(class_id, self.get_current_user()):
            record_id = self.get_argument("file_id")
            print(record_id)
            record = db.files.get_record(record_id)
            
            if record['class_id'] != class_id:
                self.write("This file does not belong to this class")
                return
            
            db.files.remove_record(record_id)
            #Delete file from disk
            name = record['name']
            upload_path = os.path.join(static_path, "files", class_id)
            file_path = os.path.join(upload_path, name)
            os.remove(file_path)
            
            self.redirect(self.reverse_url("Files", urllib.quote(class_id)))
        else:
            self.write("Insufficient Permissions")
            
class FileTags(BaseHandler):
    template = env.get_template('files/file_tags.template')
    @authenticated
    @check_prof
    def get(self, class_id, record_id):
        class_id = db.files.get_class_id_for_record(record_id)
        if db.classes.check_instructor_and_tas(class_id, self.get_current_user()):
            record = db.files.get_record(record_id)
            tagged = record['tags']
            untagged = db.files.get_untagged(record_id)
            #Sort by date
            tagged = sorted(tagged, cmp=lambda x,y: cmp(x['start'], y['start']))
            untagged = sorted(untagged, cmp=lambda x,y: cmp(x['start'], y['start']))
            self.write(self.template.render(tagged=tagged, untagged=untagged))
        else:
            self.write("Insufficient Permissions")
            
    @authenticated
    @check_prof
    def post(self, class_id, record_id):
        class_id = db.files.get_class_id_for_record(record_id)
        if db.classes.check_instructor_and_tas(class_id, self.get_current_user()):
            #TODO: Check that the record and event belong to the same class?
            untag_event_ids = self.get_arguments("untag_event_id")
            tag_event_ids = self.get_arguments("tag_event_id")
            if tag_event_ids:
                db.files.add_tags(record_id, tag_event_ids)
            if untag_event_ids:
                db.files.remove_tags(record_id, untag_event_ids)
            self.redirect(self.reverse_url('FileTags', class_id, record_id))
        else:
            self.write("Insufficient Permissions")