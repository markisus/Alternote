from src.db.collections import *

def create_school(school_name, tags=[]):
    return schools.insert({'_id':school_name, 'name':school_name, 'tags':tags})

def get_schools():
    return schools.find()
