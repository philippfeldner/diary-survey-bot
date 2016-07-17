import os

participants = []

time_keyboard = [['✅ 06:00', '❎ 06:00'], ['✅ 08:00', '❎ 08:00'],
                 ['✅ 10:00', '❎ 10:00'], ['✅ 12:00', '❎ 12:00'],
                 ['✅ 14:00', '❎ 14:00'], ['✅ 16:00', '❎ 16:00'],
                 ['✅ 18:00', '❎ 18:00'], ['✅ 20:00', '❎ 20:00'],
                 ['Fertig!']]


class Participant:
    day_count = 0
    language = None
    chat_id = None
    wait_for_reply = False
    time_t = None

    def __init__(self, chat_id=None):
        self.id = chat_id
        if self.chat_id is None:
            open('in_progress/part' + str(self.chat_id) + '.json')

    def check_survey_complete(self):
        if self.day_count == 10: # get amount of questions from settings
            os.rename('in_progress/part' + str(self.chat_id) + '.json',
                      'completed/' + str(self.chat_id) + '.json')
            # Todo: maybe notify admins


    def save_data(self):
        # Todo: Check if file existent
        # Todo: Json!
        # Todo: Care for dataloss!
        data = open('in_progress/part' + str(self.chat_id) + '.json', 'r')
        return








