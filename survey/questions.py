from datetime import datetime
from admin.settings import schedule_points

from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardHide
from telegram.ext import Job, JobQueue

from survey.data_set import DataSet
from survey.participant import Participant
from survey.keyboard_presets import CUSTOM_KEYBOARDS

import random


LANGUAGE, COUNTRY, GENDER, TIME_T, TIME_OFFSET = range(5)


def calc_delta_t(time, days):
    hh = time[:2]
    mm = time[3:]
    current = datetime.now()
    future = datetime(current.year, current.month, current.day, int(hh), int(mm))
    seconds = future - current
    if days > 0 and seconds.seconds < 86400:
        return seconds.seconds + 86400 + ((days - 1) * 86400)
    elif days > 0 and seconds.seconds > 86400:
        return seconds.seconds + ((days - 1) * 86400)
    else:
        return seconds.seconds


def calc_block_time(time_t):
    try:
        interval = schedule_points[time_t]
    except KeyError:
        return 0

    hh_start = int(interval[0][:2])
    hh_end = int(interval[1][:2])
    mm_begin = int(interval[0][3:])
    mm_end = int(interval[1][3:])

    if hh_start < hh_end:
        value_hh = random.randint(hh_start, hh_end)
        if value_hh == hh_start:
            value_mm = random.randint(mm_begin + 10, 59)
        elif value_hh == hh_end:
            value_mm = random.randint(0, mm_end)
        else:
            value_mm = random.randint(0, 59)

    elif hh_start == hh_end:
        value_hh = hh_start
        value_mm = random.randint(mm_begin + 10, mm_end - 10)
    else:
        value_hh = random.choice[random.randint(hh_start, 23), random.randint(0, hh_end)]
        if value_hh == hh_start:
            value_mm = random.randint(mm_begin + 10, 59)
        elif value_hh == hh_end:
            value_mm = random.randint(0, mm_end)
        else:
            value_mm = random.randint(0, 59)

    return str(value_hh).zfill(2) + ':' + str(value_mm).zfill(2)


def question_handler(bot: Bot, update: Update, user_map: DataSet, job_queue: JobQueue):
    try:
        # Get the user from the dict and its question_set (by language)
        user = user_map.participants[update.message.chat_id]  # type: Participant

        # Case for very first question.
        if user.question_ == -1:
            user.set_language(update.message)
            user.set_block(0)
            q_set = user_map.return_question_set_by_language(user.language_)
            user.q_set_ = q_set
            current_day = q_set[0]["day"]
            user.set_day(current_day)
            user.set_question(0)
            user.set_block(0)
            user.increase_pointer()
        elif user.q_idle_:
            q_set = user.q_set_
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

            store_answer(user, update.message.text, q_prev, b_prev)  # Todo more info
            if user.check_finished():
                return

            user.set_q_idle(False)
        else:
            # User has send something without being asked a question.
            return
    except KeyError as error:
        print(error)
        return

    question, time = find_next_question(user)
    if time == 0:
        message = question["text"]
        q_keyboard = get_keyboard(question["choice"])
        bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=q_keyboard)
        user.increase_question()
        user.set_q_idle(True)
    else:
        user.block_complete_ = True
        next_day = user.set_next_block()
        element = user.next_block[2]
        day_offset = next_day - user.day_
        time_t = calc_block_time(element["time"])
        due = calc_delta_t(time_t, day_offset)

        new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
        job_queue.put(new_job)


def store_answer(user, message, question):
    # Todo test
    condition = question["condition"]
    if message in question["condition"]:
        user.add_conditions(condition)
    # Todo: CSV stuff
    return


def queue_next(bot: Bot, job: Job):
    print('new job')
    user = job.context[0]  # type: Participant
    job_queue = job.context[1]
    user.block_complete_ = False
    q_set = user.q_set_
    user.question_ = 0
    user.pointer_ = user.next_block[0]
    user.block_ = user.next_block[1]
    element = user.next_block[2]

    # Check if the user is currently active
    if not user.active_:
        return

    try:
        # Find next question that the user should get.
        while not user.check_requirements(element["questions"][user.question_]):
            user.increase_question()
    except IndexError:
        # User did not fulfill any questions for the day so we reschedule.
        # Set the new day.
        next_day = user.set_next_block()
        element = user.next_block[2]
        day_offset = next_day - user.day_
        time_t = calc_block_time(element["time"])
        due = calc_delta_t(time_t, day_offset)

        # Add new job and to queue. The function basically calls itself recursively after x seconds.
        new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
        job_queue.put(new_job)
        return

    # Sending the question
    question = q_set[user.pointer_]["blocks"][user.block_]["questions"][user.question_]

    q_text = question["text"]
    q_keyboard = get_keyboard(question["choice"])
    bot.send_message(user.chat_id_, q_text, reply_markup=q_keyboard)
    user.set_q_idle(True)

    # Check if there is a reason to queue again.
    if not user.auto_queue_ or not user.block_complete_:
        return

    # Calculate seconds until question is due.
    next_day = user.set_next_block()
    element = user.next_block[2]
    day_offset = next_day - user.day_
    time_t = calc_block_time(element["time"])
    due = calc_delta_t(time_t, day_offset)

    new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
    job_queue.put(new_job)
    return


def find_next_question(user):
    q_set = user.q_set_
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
                question = find_next_question(user)
            return question, offset
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
                    question = find_next_question(user)
                return question, offset
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


