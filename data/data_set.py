import json
from admin.settings import default_language


class DataSet:
    participants = {}
    q_set_de_ = None
    q_set_en_ = None
    q_set_es_ = None
    q_set_fr_ = None

    def __init__(self):
        try:
            self.q_set_de_ = json.load('question_set_de.json')
        except FileNotFoundError:
            print('Language: German not available!')
        try:
            self.q_set_en_ = json.load('question_set_en.json')
        except FileNotFoundError:
            print('Language: English not available!')
        try:
            self.q_set_es_ = json.load('question_set_es.json')
        except FileNotFoundError:
            print('Language: Spanish not available!')
        try:
            self.q_set_fr_ = json.load('question_set_fr.json')
        except FileNotFoundError:
            print('Language: French not available!')
        return

    def get_participant(self, chat_id):
        return self.participants[chat_id]

    def add_participant(self, user):
        self.participants[user.chat_id] = user
        return

    def return_question_set_by_language(self, lang):
        if lang == 'de' and self.q_set_de_ is not None:
            return self.q_set_de_
        elif lang == 'en' and self.q_set_en_ is not None:
            return self.q_set_en_
        elif lang == 'es' and self.q_set_es_ is not None:
            return self.q_set_es_
        elif lang == 'fr' and self.q_set_fr_ is not None:
            return self.q_set_fr_
        else:
            return self.return_question_set_by_language(default_language)
