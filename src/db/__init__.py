#from collections import *
#
##
##from collections import *
##from schools import *
##from utils import *
##
##def clean_collections():
##    users.remove()
##    events.remove()
##    posts.remove()
##    classes.remove()
##    logins.remove()
##    schools.remove()
##    
#def populate():
#    print("This will destroy the current database. Press a key to continue")
#    raw_input()
#    
#    #clean_collections()
#    
#    cs1 = create_class("Columbia", "Alfred Aho", "Intro to CS", "1", "2012-05-11")
#    print("Created classes")
#
#    Anonymous = create_user("Anonymous", "", "admin", "Anonymous", None, "student")
#    Mark = create_user("Mark", "Liu", "admin", "ml2877@columbia.edu", "Columbia", type="student")
#    Amanda = create_user("Amanda", "Pickering", "test", "amanda@columbia.edu", "Columbia", type="admin")
#    Ankit = create_user("Ankit", "Shah", "admin", "ankit@upenn.edu", "U. Penn", type="professor")
#    print("Created users")
#    
#    register_user_for_class(Mark, cs1)
#    register_user_for_class(Amanda, cs1)
#    register_user_for_class(Ankit, cs1)
#
#    print("Registered users for some classes")
#    
#    lecture1 = create_event_for_class(cs1, "Lecture", "Hamilton 207", datetime(2011, 9, 6, 13, 40).isoformat(), datetime(2011, 9, 6, 15).isoformat(), "The first lecture!")
#    print("Created event for a class")
#        
#    print("Done")
##
###Test functionality when this file is run as a standalone program:
#if __name__ == '__main__': populate()