import os
import sqlite3

INIT, SET_1, SET_2, ADDITIONAL, FEEDBACK = range(5)
db = sqlite3.connect('participants.db')


class Participant:
    chat_id = None
    language = None
    gender = None
    country = None
    day_count = 0
    time_t = None
    time_offset = 0

    var_cond_1 = False
    var_cond_2 = False
    var_cond_3 = False
    var_cond_4 = False

    set = None
    set_complete = False
    set_count = 0

    def __init__(self, chat_id=None):
        self.id = chat_id
        if self.chat_id is None:
            db.execute("INSERT INTO participants (ID) VALUES (?)", chat_id)
            db.execute("INSERT INTO participants (cond_4, cond_3, cond_2, "
                       "cond_1, time_offset, time_t, day_t, country, gender, "
                       "language) DEFAULT VALUES")

    def check_survey_complete(self):
        if self.day_count == 10: # get amount of questions from settings
            os.rename('in_progress/part' + str(self.chat_id) + '.json',
                      'completed/' + str(self.chat_id) + '.json')
        return 0

    def delete_participant(self):
        db.execute("DELETE FROM participants WHERE ID=?", self.chat_id)
        return 0


    def save_data(self):
        data = open('in_progress/part' + str(self.chat_id) + '.json', 'r')
        return












