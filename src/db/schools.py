from collections import *

def create_school(school_name, tags=[]):
    return schools.insert({'_id':school_name, 'tags':tags})