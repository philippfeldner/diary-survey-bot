from datetime import datetime

from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardHide
from telegram.ext import Job, JobQueue

from survey.data_set import DataSet
from survey.participant import Participant

LANGUAGE, COUNTRY, GENDER, TIME_T, TIME_OFFSET = range(5)


def calc_delta_t(time, days):
    hh = time[2:]
    mm = time[:2]
    # Todo: Check correctness
    current = datetime.now()
    future = datetime(current.year, current.month, current.day + days, int(hh), int(mm))
    seconds = future - current
    return seconds.seconds


def question_handler(bot: Bot, update: Update, user_map: DataSet, job_queue: JobQueue):
    # Get the user from the dict and its question_set (by language)

    try:
        user = user_map.participants[update.message.chat_id]  # type: Participant

        # Case for very first question.
        if user.question_id_ == -1:
            user.set_language(update.message)
            q_set = user_map.return_question_set_by_language(user.language_)
            question_id = user.increase_question_id()
            q_current = q_set[question_id]
        # Case if the user was actually asked a question.
        elif user.q_idle_:
            q_set = user_map.return_question_set_by_language(user.language_)
            # Get the matching question for the users answer.
            q_prev = q_set[user.question_id_]
            store_answer(user.chat_id_, update.message, q_prev)

            question_id = user.increase_question_id()

            # Check if user has completed the whole survey
            if user.question_id_ == len(q_set):
                user.finished()
                # Todo: Send message and stuff

            q_current = q_set[question_id]
            user.q_idle_ = False
        else:
            # Todo: Is this enough?
            return
    except KeyError:
        # Todo handle exception
        return

    # find next question for the user
    while not user.requirements(q_current['conditions']):
        question_id = user.increase_question_id()
        q_current = q_set[question_id]

    if not user.parse_commands(q_current['commands'], update.message):
        # Todo more features maybe?
        return

    if q_current['day'] != user.day_:
        user.day_complete_ = True

    # if there is no auto_queue enabled and the user has answered all questions
    # for the day a job for the next day gets scheduled.
    if not user.auto_queue_ and user.day_complete_:
        job = Job(queue_next, context=[user, question_id, q_set, job_queue])
        job_queue.put(job)
        return

    # No more questions for today
    if user.day_complete_:
        return

    message = q_current['question']
    reply_markup = get_keyboard(q_current['choice'])
    bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=reply_markup)
    user.q_idle_ = True


def store_answer(chat_id, message, question):
    # Todo: Check if condition is to be set; Check if a "main" attribute is to be stored.
    return


def queue_next(bot: Bot, job: Job):
    user = job.context[0]
    question_id = job.context[1]
    q_set = job.context[2]
    job_queue = job.context[3]

    if not user.active_:
        return

    if question_id is not None and user.requirements(q_set[question_id]["conditions"]):  # Todo look into
        q_text = q_set[question_id]["question"]
        q_keyboard = get_keyboard(q_set[question_id]["choice"])
        bot.send_message(user.chat_id_, q_text, reply_markup=q_keyboard)

    if not user.auto_queue_ or not user.day_complete_:
        # Todo maybe do stuff here
        return

    day = user.day_
    question_id = user.question_id_

    # Find next question that is not ment for the current day
    while q_set[question_id]['day'] == day:
        question_id += 1

    # Calculate seconds until question is due.
    day_offset = q_set[question_id] - day
    due = calc_delta_t(user.time_t_, day_offset)

    # Add new job and to queue. The function basically calls itself recursively after x seconds.
    new_job = Job(queue_next, due)
    job_queue.put(new_job)
    return


def get_keyboard(choice):
    #Todo
    return 0


