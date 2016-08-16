from datetime import datetime
from hashlib import sha256

from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardHide
from telegram.ext import Job, JobQueue

from survey.data_set import DataSet
from survey.participant import Participant
from survey.keyboard_presets import CUSTOM_KEYBOARDS


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
    try:
        # Get the user from the dict and its question_set (by language)
        user = user_map.participants[update.message.chat_id]  # type: Participant

        # Case for very first question.
        if user.question_ == -1:
            user.set_language(update.message)
            user.set_block(0)
            q_set = user_map.return_question_set_by_language(user.language_)
            current_block = q_set[0]["blocks"][user.block_]
            current_day = q_set[0]["day"]
            user.set_day(current_day)
            d_prev = current_day
            b_prev = 0
            q_prev = -1
        elif user.q_idle_:
            q_set = user_map.return_question_set_by_language(user.language_)
            # Get the matching question for the users answer.

            pointer = user.pointer_
            d_prev = q_set[pointer]
            b_prev = d_prev["block"][user.block_]
            q_prev = b_prev["questions"][user.question_]

            if not valid_answer(q_prev, update.message):
                message = q_prev["text"]
                reply_markup = get_keyboard(q_prev["choice"])
                bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=reply_markup)
                user.set_q_idle(True)
                return
            # Storing the answer and moving on the next question
            store_answer(user, update.message.text, q_prev)  # Todo more info
            if user.check_finished():
                return

            user.set_q_idle(False)
        else:
            # User has send something without being asked a question.
            return
    except KeyError as error:
        print(error)
        return

    question, time = find_next_question(user, q_set)
    if time == 0:
        message = question["text"]
        q_keyboard = get_keyboard(question["choice"])
        bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=q_keyboard)
        user.set_q_idle(True)
    elif not user.auto_queue_:
        queue_next()  # Todo
    else:
        return


def store_answer(user, message, question):
    condition = [message, question['id']]
    if message in question['conditions']:
        user.add_conditions(condition)
    # Todo: CSV stuff
    return


def queue_next(bot: Bot, job: Job):
    print('new job')
    user = job.context[0]  # type: Participant
    q_set = job.context[2]
    job_queue = job.context[3]
    user.day_complete_ = False
    day = user.day_

    # Check if the user is currently active
    if not user.active_:
        return

    try:
        # Find next execution block
        element = user.next_block[2]
        question = 0
        # Find next question that the user should get.
        while not user.check_requirements(element["questions"][question]):
            question += 1
    except IndexError:
        # User did not fulfill any questions for the day so we reschedule.
        # Set the new day.
        user.day_ = user.set_next_block(q_set)

        # Calculate seconds until question is due.
        day_offset = q_set[question_id] - day
        due = calc_delta_t(user.time_t_, day_offset)
        # TODO
        # Add new job and to queue. The function basically calls itself recursively after x seconds.
        new_job = Job(queue_next, 60, repeat=False, context=[user, question_id, q_set, job_queue])
        job_queue.put(new_job)
        return

    # Sending the question
    pointer = element[0]
    block = element[1]

    question = q_set[pointer]["blocks"][block]["questions"][question]

    q_text = question["text"]
    q_keyboard = get_keyboard(question["choice"])
    bot.send_message(user.chat_id_, q_text, reply_markup=q_keyboard)
    user.set_q_idle(True)

    # Check if there is a reason to queue again.
    if not user.auto_queue_ or not user.day_complete_:
        return

    user.question_ = question

    day = user.set_next_block(q_set)

    # Calculate seconds until question is due.
    day_offset = q_set[question_id] - day
    due = calc_delta_t(user.time_t_, day_offset)

    # Add new job and to queue. The function basically calls itself recursively after x seconds.
    new_job = Job(queue_next, 60, repeat=False, context=[user, pointer, block, q_set, job_queue])
    job_queue.put(new_job)
    return


def find_next_question(user, q_set):
    try:
        q_day = q_set[user.pointer_]
        q_block = q_day["blocks"][user.block_]
        question = q_block[user.increase_question()]
        while user.check_requirements(question):
            question = q_block[user.increase_question()]
        return question, 0
    except IndexError:
        try:
            q_day = q_set[user.pointer_]
            q_block = q_day["blocks"][user.increase_block()]
            question = q_block[user.set_question(0)]
            try:
                while user.check_requirements(question):
                    question = q_block[user.increase_question()]
            except IndexError:
                user.increase_block()
                user.set_question(0)
                question = find_next_question(user, q_set)
            return question  # Todo: Time!
        except IndexError:
            try:
                q_day = q_set[user.increase_pointer()]
                q_block = q_day["blocks"][user.set_block(0)]
                question = q_block[user.set_question(0)]
                try:
                    while user.check_requirements(question):
                        question = q_block[user.increase_question()]
                except IndexError:
                    user.increase_pointer()
                    user.set_block(0)
                    user.set_question(0)
                    question = find_next_question(user, q_set)
                return question  # Todo: Time!
            except IndexError:
                return


def get_keyboard(choice):
    if choice == []:
        return ReplyKeyboardHide()
    elif choice[0] == 'KEY_1':
        return ReplyKeyboardMarkup(CUSTOM_KEYBOARDS['KEY_1'])
    else:
        return ReplyKeyboardMarkup(choice)


def valid_answer(question, message):
    commands = question['commands']
    if 'FORCE_KB_REPLY' not in commands or question['choice'] == []:
        return True
    try:
        choice = CUSTOM_KEYBOARDS[question['choice'][0]]
    except KeyError:
        choice = question['choice']

    if message in choice:
        return True
    else:
        return False


