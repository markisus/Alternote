from env import BaseHandler, env, check_prof
from tornado.web import authenticated
from constants import static_path
import os
from forms.forms import FileForm
import db.classes
import db.files
import urllib
#File Uploading/Management


class Files(BaseHandler):
    template = env.get_or_select_template("files/edit_files.template")

    @authenticated
    @check_prof    
    def get(self, class_id):
        if db.classes.check_instructor_and_tas(class_id, self.get_current_user()):
            files = db.files.get_records(class_id)
            sorted_files = sorted(files, cmp=lambda x,y: cmp(x['name'], y['name'])) #Lexicographic sort
            navbar = self.render_navbar(class_id, True)
            sidebar = self.render_sidebar(class_id)
            self.write(self.template.render(form=FileForm(), files=sorted_files, class_id=class_id, navbar=navbar, sidebar=sidebar))
        else:
            self.write("Insufficient Permissions")

    @authenticated
    @check_prof        
    def post(self, class_id):
        if db.classes.check_instructor_and_tas(class_id, self.get_current_user()):
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
        else:
            self.write("Insufficient Permissions")
            
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
            navbar = self.render_navbar(class_id, True)
            self.write(self.template.render(tagged=tagged, untagged=untagged, navbar=navbar))
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