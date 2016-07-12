import os



class Participant:
    day_count = 0
    language = None
    chat_id = None

    def __init__(self, chat_id=None):
        self.id = chat_id
        if self.chat_id is None:
            open('in_progess/' + 'part' + str(self.chat_id) + '.json')

    def check_survey_complete(self):
        if self.day_count == 10: # get amount of questions from settings
            os.rename('in_progess/' + 'part' + str(self.chat_id) + '.json',
                      'completed/' + 'part' + str(self.chat_id) + '.json')
            # Todo: maybe notify admins







