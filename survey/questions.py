from datetime import datetime

from telegram import Bot, Update

from survey.data_set import DataSet
from survey.participant import Participant

LANGUAGE, COUNTRY, GENDER, TIME_T, TIME_OFFSET = range(5)


def calc_delta_t(time, days):
    hh = time[2:]
    mm = time[:2]

    current = datetime.now()
    future = datetime(current.year, current.month, current.day + days, int(hh), int(mm))
    seconds = future - current
    return seconds


def question_handler(bot: Bot, update: Update, user_map: DataSet):
    # Get the user from the dict and its question_set (by language)
    user = user_map.participants[update.message.chat_id]
    q_set = user_map.return_question_set_by_language(user.language_)

    # Get the matching question for the users answer.
    q_prev = q_set[user.question_id_]
    store_answer(user.chat_id_, update.message, q_prev)

    # Load next question
    question_id = user.increase_question_id()
    q_current = q_set[question_id]

    # find next question for the user
    while not user.requirements(q_current['conditions']):
        question_id = user.increase_question_id()
        q_current = q_set[question_id]

    if q_current['day'] == user.day_:
        bot.send_message() # Todo
    else:

        day_offset = q_current[1] - user.day_









def get_base_info(bot: Bot, update: Update, user: Participant):
    return


def store_answer(chat_id, message, question):
    # Todo: Check if condition is to be set; Check if a "main" attribute is to be stored.
    return


