from db.collections import *
from random import randint

word_bank = """academic, augur, bookish person, bookworm, brain, critic, disciple, 
doctor, egghead, gnome, grind, intellectual, learned person, 
learner, litterateur, person of letters, philosopher, professor, pupil, 
sage, savant, schoolchild, scientist, student, teacher, 
wise person, big cheese, connoisseur, 
guru, professor, pundit, scholar , specialist, textbook,  veteran, virtuoso, whiz, wizard, 
Einstein, academician, doctor, egghead, genius, highbrow, intellect, intellectual, 
mastermind, prodigy, pundit, sage, scholar"""
word_bank = [word.strip().replace(" ", "-") for word in word_bank.split(",")]

def create_student_code(class_id):
    
    id = "student-" + __randword() + "-of-" + class_id
    codes.insert({"_id":id, "class_id":class_id, "type":"student"})

def create_ta_code(class_id):
    id = "master-" + __randword() + "-of-" + class_id
    codes.insert({"_id":id, "class_id":class_id, "type":"ta"})

def lookup_codes(class_id):
    result = codes.find({'class_id':class_id})
    return result

def lookup_code(code_id):
    result = codes.find_one({'_id':code_id})
    if not result:
        raise KeyError("Code " + code_id + " does not exist!")
    else:
        return result
    
def __randword():
    if not word_bank:
        return "?"
    rand = randint(0, len(word_bank)-1)
    return word_bank[rand]
