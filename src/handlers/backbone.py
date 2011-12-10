from env import BaseHandler, env
import db.files
import db.calendar
import datetime
import json

#Utility methods for interfacing with Backbone################
def rename_key(adict, prev_key, new_key):
    val = adict[prev_key]
    del adict[prev_key]
    adict[new_key] = val

def doc_to_Backbone(doc):   
    rename_key(doc, '_id', 'id')

def doc_to_Mongo(doc):
    rename_key(doc, 'id', '_id')
    
def collection_to_Backbone(dicts):
    for adict in dicts:
        doc_to_Backbone(adict)

def collection_to_Mongo(dicts):
    for adict in dicts:
        doc_to_Mongo(adict)
#End Utility methods for interfacing with Backbone#############

class Bootstrap(BaseHandler):
    template = env.get_template("backbone_app.template")
    
    def get(self, class_id):
        #Get user_id
        user_id = self.get_current_user()
        
        #Get class_doc for this class
        class_doc = db.classes.get_class(class_id)
        class_doc = json.dumps(class_doc, default=str)
        
        #Get files for this class
        files = db.files.get_records(class_id)
        collection_to_Backbone(files)
        files = json.dumps(files, default=str)
        
        #Get calendar events for this class
        events = db.calendar.get_all(class_id)
        collection_to_Backbone(events)
        events = json.dumps(events, default=str)
        
        self.render_out(server_timestamp=datetime.datetime.now().isoformat()[:16], user_id=user_id, class_id=class_id, class_doc=class_doc, files=files, events=events)
        
#Backbone Collection Handlers
class Events(BaseHandler):
    def get(self, class_id, event_id=None):
        if not event_id:
            events = db.calendar.get_all(class_id)
            collection_to_Backbone(events)
            self.write(json.dumps(events, default=str))
            return
        else:
            event = db.calendar.get_item(event_id)
            if str(event['class']['_id']) != class_id:
                raise KeyError("Wrong class")
            doc_to_Backbone(event)
            self.write(json.dumps(event, default=str))
            return

    def post(self, class_id, event_id=None):
        body = self.request.body
        doc = json.loads(body)
        event_id = db.classes.create_event_for_class(class_id, **doc)
        doc['id'] = str(event_id)
        self.write(json.dumps(doc, default=str))
        
    def put(self, class_id, event_id):
        print("Received put")
        body = self.request.body
        doc = json.loads(self.request.body)
        del doc['class'] #Avoid dealing with deserializing the class doc; this shouldn't change anyway
        doc_id = doc.pop("id")
        db.calendar.edit_item(doc_id, doc)
        print(self.get_params())
    
    def delete(self, class_id, event_id):
        print("Received delete")
        db.calendar.delete_item(event_id)
        
class Files(BaseHandler):
    def get(self, class_id):
        print("GET called for " + str(class_id))