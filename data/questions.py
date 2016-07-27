import json

from data.data_set import DataSet
from user.participant import Participant
from telegram import Bot, Update

from user import Participant

LANGUAGE, COUNTRY, GENDER, TIME_T, TIME_OFFSET = range(5)


def question_handler(bot: Bot, update: Update, user_map: DataSet):
    user = user_map.participants[update.message.chat_id]  # type: Participant
    question_id = user.question_id_


def get_base_info(bot: Bot, update: Update, user: Participant):
    return


