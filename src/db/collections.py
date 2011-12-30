from bson.objectid import ObjectId
from pymongo import Connection, ASCENDING
from pymongo.errors import *

print("Connecting to MongoDB")
default_connection = ('localhost', 27017)
connection = Connection(*default_connection)
print("Connected")
alternote = connection.alternote

#Binding collection names and setting indices
schools = alternote.schools

users = alternote.users
users.ensure_index([('_id',1), ('first_name',1), ('last_name',1)]) #For covered queries
users.ensure_index([('_id',1), ('flagged', 1)])
users.ensure_index([('_id',1), ('upvoted', 1), ('flagged', 1)])

events = alternote.events
events.ensure_index([('class._id',1)])

posts = alternote.events.posts
posts.ensure_index([('comment._id',1)])
posts.ensure_index([('event',1),('timestamp',1)])
posts.ensure_index([('_id',1), ('name',1)], [('university',1), ('tags',1)])

classes = alternote.classes

calendar = alternote.calendar

logins = alternote.logins
logins.ensure_index([('userid',1)])

codes = alternote.codes

files = alternote.files

avatars = alternote.avatars