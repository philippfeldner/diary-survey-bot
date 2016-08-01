import pickle
import sqlite3
import time
from telegram.ext import JobQueue
from survey.data_set import DataSet
from admin import settings


class Participant:
    chat_id_ = 0
    language_ = ''
    gender_ = ''
    country_ = ''
    day_ = 1
    time_t_ = ''
    time_offset_ = 0xFFFF
    conditions_ = []
    question_id_ = -1

    auto_queue_ = False
    day_complete_ = False
    q_idle_ = False
    active_ = True

    def __init__(self, chat_id=None, init=True):
        self.chat_id_ = chat_id
        if init:
            try:
                db = sqlite3.connect('survey/participants.db')
                db.execute("INSERT INTO participants (ID, conditions, time_t,"
                           "country, gender, language, question_id, time_offset, day)"
                           "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (chat_id, pickle.dumps([]), '', '', '', '', -1, 0xFFFF, -1))
                db.commit()
                db.close()
                text = "User:\t" + str(self.chat_id_) + "\tregistered.\t" + time.strftime("%X %x\n")
                try:
                    with open('log.txt', 'a') as log:
                        log.write(text)
                except OSError or IOError as error:
                    print(error)
            except sqlite3.Error as error:
                print(error)

    def set_language(self, language):
        if language == ('Deutsch' or 'de'):
            lang = 'de'
        elif language == ('English' or 'en'):
            lang = 'en'
        elif language == ('Espagnol' or 'es'):
            lang = 'es'
        elif language == ('Francais' or 'fr'):
            lang = 'fr'
        else:
            lang = settings.default_language

        self.language_ = lang
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("UPDATE participants SET language=? WHERE ID=?", (lang, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return

    def set_gender(self, gender):
        self.gender_ = gender
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("UPDATE participants SET gender=? WHERE ID=?", (gender, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return

    def set_country(self, country):
        self.country_ = country
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("UPDATE participants SET country=? WHERE ID=?", (country, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return

    def set_day(self, day):
        self.day_ = day
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("UPDATE participants SET day_t=? WHERE ID=?", (self.day_, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return self.day_

    def set_time_t(self, time_t):
        self.time_t_ = time
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("UPDATE participants SET time_t=? WHERE ID=?", (time_t, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return

    def set_time_offset(self, offset):
        self.time_offset_ = offset
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("UPDATE participants SET time_offset=? WHERE ID=?", (offset, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return

    def add_conditions(self, conditions):
        if conditions == []:
            return
        self.conditions_ += conditions
        try:
            db = sqlite3.connect('survey/participants.db')
            cursor = db.cursor()
            cursor.execute("SELECT conditions FROM participants WHERE ID=?", self.chat_id_)
            fetch = cursor.fetchone()  # type: list
            cond_blob = fetch[0]  # type: pickle
            cond_old = pickle.loads(cond_blob)
            cond = pickle.dumps(cond_old + conditions)
            db.execute("UPDATE participants SET conditions=? WHERE ID=?", (cond, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return

    def increase_question_id(self):
        self.question_id_ += 1
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("UPDATE participants SET question_id=? WHERE ID=?", (self.question_id_, self.chat_id_))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        return self.question_id_

    def delete_participant(self):
        try:
            db = sqlite3.connect('survey/participants.db')
            db.execute("DELETE FROM participants WHERE ID=?", (self.chat_id_,))
            db.commit()
            db.close()
        except sqlite3.Error as error:
            print(error)
        text = "User:\t" + str(self.chat_id_) + "\tunregistered.\t" + time.strftime("%X %x\n")
        try:
            with open('log.txt', 'a') as log:
                log.write(text)
        except OSError or IOError as error:
            print(error)
        return 0

    def requirements(self, condition):
        return True
        if condition == [] or condition in self.conditions_:
            return True
        else:
            return False

    def parse_commands(self, commands, message):
        return True

    def finished(self):
        return


def initialize_participants(job_queue: JobQueue):
    user_map = DataSet()
    try:
        db = sqlite3.connect('survey/participants.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM participants ORDER BY (ID)")
        participants = cursor.fetchall()
        # print(participants)
        for row in participants:
            user = Participant(row[0], init=False)
            user.conditions_ = pickle.loads(row[1])
            user.time_t_ = row[2]
            user.country_ = row[3]
            user.gender_ = row[4]
            user.language_ = row[5]
            user.init_state_ = row[6]
            user.time_offset_ = row[7]
            user.day_ = row[8]
            user_map.participants[row[0]] = user
            # if user.time_t_ == '':
            #    return  # TODO
            # else:
            #    job_queue  # TODO
    except sqlite3.Error as error:
        print(error)
    return user_map


def clean_database():
    return
    # Todo


















