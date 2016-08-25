import sqlite3
import pickle

from datetime import datetime
from pytz import timezone
import random
import csv

from admin.settings import SCHEDULE_INTERVALS
from admin.settings import QUICK_TEST
from admin.debug import debug

from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardHide, Emoji
from telegram.ext import Job, JobQueue

from survey.data_set import DataSet
from survey.participant import Participant
from survey.keyboard_presets import CUSTOM_KEYBOARDS
from survey.keyboard_presets import TRANSLATE_EMOJI
import survey.keyboard_presets as kb_presets


# Calculates seconds until a certain hh:mm
# event. Used for the job_queue mainly.
# Timezones are already handled.
def calc_delta_t(time, days, zone=None):
    # If the admin setting QUICK_TEST the block scheduling ist 60s
    if QUICK_TEST is not False:
        return QUICK_TEST
    hh = time[:2]
    mm = time[3:]

    # Todo: Maybe catch timezone exception
    if zone is not None:
        current = datetime.now(timezone(zone))
    else:
        current = datetime.now()
    future = datetime(current.year, current.month, current.day, int(hh), int(mm))
    offset = future - current
    if offset.days == 0:
        return offset.seconds + 86400 + ((days - 1) * 86400)
    else:
        return offset.seconds + ((days - 1) * 86400)


# Generates a random time offset
# for the next block that shall be scheduled.
# The intervals are defined in admin/settings.py
def calc_block_time(time_t):
    try:
        interval = SCHEDULE_INTERVALS[time_t]
    except KeyError:
        return 0  # Todo

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


# This function does the main handling of
# user questions and answers.
# This is function is registered in the Dispatcher.
def question_handler(bot: Bot, update: Update, user_map: DataSet, job_queue: JobQueue):
    try:
        # Get the user from the dict and its question_set (by language)
        user = user_map.participants[update.message.chat_id]  # type: Participant

        # Case for very first question.
        if user.question_ == -1:
            user.set_active(True)
            user.set_language(update.message.text)
            user.set_block(0)
            q_set = user_map.return_question_set_by_language(user.language_)
            user.q_set_ = q_set
            current_day = q_set[0]["day"]
            user.set_day(current_day)
            user.set_block(0)
        elif user.q_idle_:
            q_set = user.q_set_
            # Get the matching question for the users answer.

            pointer = user.pointer_
            d_prev = q_set[pointer]

            b_prev = d_prev["blocks"][user.block_]
            q_prev = b_prev["questions"][user.question_]

            if not valid_answer(q_prev, update.message.text, user):
                user.set_q_idle(True)
                return
            # Storing the answer and moving on the next question

            store_answer(user, update.message.text, q_prev, job_queue)
            # Todo check last question
            user.set_q_idle(False)
        else:
            # User has send something without being asked a question.
            return
    except KeyError as error:
        print(error)
        return

    if not user.active_:
        return
    # Todo: Copy to /start
    question = find_next_question(user)
    if question is not None:
        message = question["text"]
        q_keyboard = get_keyboard(question["choice"], user)
        bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=q_keyboard)
        user.set_q_idle(True)
    elif user.job_ is None:
        user.block_complete_ = True
        next_day = user.set_next_block()
        element = user.next_block[2]
        day_offset = next_day - user.day_
        time_t = calc_block_time(element["time"])
        due = calc_delta_t(time_t, day_offset)

        debug('QUEUE', 'next block in ' + str(due) + ' seconds. User: ' + str(user.chat_id_), log=True)
        new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
        user.job_ = new_job
        job_queue.put(new_job)


# This function is getting used to generate
# the CSV files and store values.
# Also the conditions, DB values get set here.
def store_answer(user, message, question, job_queue):
    commands = question['commands']
    for [element] in commands:
        # -- DB TRIGGER for storing important user data -- #
        if element == "TIMEZONE":
            user.set_timezone(message)
        elif element == "COUNTRY":
            user.set_country(message)
        elif element == "GENDER":
            user.set_gender(message)
        elif element == "AGE":
            user.set_age(message)
        elif element == "STOP":
            True  # Todo
        elif element == "Q_ON":
            user.auto_queue_ = True
            next_day = user.set_next_block()
            element = user.next_block[2]
            day_offset = next_day - user.day_
            time_t = calc_block_time(element["time"])
            due = calc_delta_t(time_t, day_offset)

            debug('QUEUE', 'next block in ' + str(due) + ' seconds. User: ' + str(user.chat_id_), log=True)
            new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
            user.job_ = new_job
            job_queue.put(new_job)

    condition = question["condition"]
    if condition != [] and message in condition[0]:
        user.add_conditions(condition)

    if message in TRANSLATE_EMOJI:
        message = TRANSLATE_EMOJI[message]

    if user.timezone_ == '':
        timestamp = datetime.now().isoformat()
    else:
        # Todo: Maybe catch tz exception
        timestamp = datetime.now(timezone(user.timezone_)).isoformat()

    q_text = question['text']
    q_text.replace('\n', ' ')
    q_text.replace(';', ',')
    message.replace('\n', ' ')
    message.replace(';', ',')

    with open('survey/data_incomplete/' + str(user.chat_id_) + '.csv', 'a+') as user_file:
        columns = [user.language_, user.gender_, user.age_, user.country_, user.timezone_, user.day_, user.block_,
                   timestamp, user.question_,  q_text, message]
        writer = csv.writer(user_file, delimiter=';')
        writer.writerow(columns)

    return


# This function is called by the job_queue
# and starts all the blocks after the set time.
# It also calls itself recursively to assure progressing.
def queue_next(bot: Bot, job: Job):
    user = job.context[0]  # type: Participant
    job_queue = job.context[1]
    if not user.active_:
        return
    user.block_complete_ = False
    user.job_ = None
    user.set_question(0)
    user.set_pointer(user.next_block[0])
    user.set_block(user.next_block[1])
    element = user.next_block[2]

    user.set_day(user.q_set_[user.pointer_]['day'])

    if ['MANDATORY'] in element['settings']:
        user.auto_queue_ = False
    else:
        user.auto_queue_ = True

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
        if user.next_block is None:
            return finished(user, job_queue)

        element = user.next_block[2]
        day_offset = next_day - user.day_
        time_t = calc_block_time(element["time"])
        due = calc_delta_t(time_t, day_offset)

        # Add new job and to queue. The function basically calls itself recursively after x seconds.
        debug('QUEUE', 'next block in ' + str(due) + ' seconds. User: ' + str(user.chat_id_), log=True)
        new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
        user.job_ = new_job
        job_queue.put(new_job)
        return

    # Sending the question
    question = element["questions"][user.question_]

    q_text = question["text"]
    q_keyboard = get_keyboard(question["choice"], user)
    bot.send_message(user.chat_id_, q_text, reply_markup=q_keyboard)
    user.set_q_idle(True)

    # Check if there is a reason to queue again.
    if not user.auto_queue_:
        return

    # Calculate seconds until question is due.
    next_day = user.set_next_block()
    if user.next_block is None:
        return finished(user, job_queue)
    element = user.next_block[2]
    day_offset = next_day - user.day_
    time_t = calc_block_time(element["time"])
    due = calc_delta_t(time_t, day_offset)

    debug('QUEUE', 'next block in ' + str(due) + ' seconds. User: ' + str(user.chat_id_), log=True)
    new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
    job_queue.put(new_job)
    return


# This function returns the next
# question meant for the user.
# If the block is complete None is returned.
def find_next_question(user):
    q_set = user.q_set_
    try:
        q_day = q_set[user.pointer_]
        q_block = q_day["blocks"][user.block_]
        question = q_block["questions"]
        user.increase_question()
        while not user.check_requirements(question[user.question_]):
            user.increase_question()
        return question[user.question_]
    except IndexError:
        return None


# This function returns the ReplyKeyboard for the user.
# Either the ones from the json file are used or
# more complex ones are generated in survey/keyboard_presets.py
def get_keyboard(choice, user):
    if choice == []:
        return ReplyKeyboardHide()

    # -------- Place to register dynamic keyboards -------- #
    if choice[0][0] == 'KB_TIMEZONE':
        return ReplyKeyboardMarkup(kb_presets.generate_timezone_kb(user.country_))

    try:
        keyboard = ReplyKeyboardMarkup(CUSTOM_KEYBOARDS[choice[0][0]])
    except KeyError:
        keyboard = ReplyKeyboardMarkup(choice)

    return keyboard


# If the command FORCE_KB_REPLY is set in json the
# answer is checked if it is really a choice
# from the ReplyKeyboard.
def valid_answer(question, message, user):
    commands = question['commands']
    if ['FORCE_KB_REPLY'] not in commands or question['choice'] == []:
        return True

    if question['choice'][0][0] == 'KB_TIMEZONE':
        return ReplyKeyboardMarkup(kb_presets.generate_timezone_kb(user.country_))

    try:
        choice = CUSTOM_KEYBOARDS[question['choice'][0][0]]
    except KeyError:
        choice = question['choice']

    if [message] in choice:
        return True
    else:
        return False


# This functions handles the very last question.
# It allows the user to finish its question within
# 24 hours. Afterwards finalize() is called.
def finished(user, job_queue):
    user.last_ = True
    new_job = Job(finalize, 86400, repeat=False, context=user)
    job_queue.put(new_job)
    return


# If the user reaches this function he has successfully
# completed the survey. The clean up is done here
# and the he gets set to passive.
def finalize(bot: Bot, job: Job):
    user = job.context
    user.set_active = False
    # Todo File saving, maybe a final message
    return


def continue_survey(user, bot, job_queue):
    user.active_ = True
    q_set = user.q_set_
    q_day = q_set[user.pointer_]
    q_block = q_day["blocks"][user.block_]
    question = q_block["questions"][user.question_]
    if question is not None:
        message = question["text"]
        q_keyboard = get_keyboard(question["choice"], user)
        bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=q_keyboard)
        user.set_q_idle(True)

    if user.job_ is None:
        user.block_complete_ = True
        next_day = user.set_next_block()
        element = user.next_block[2]
        day_offset = next_day - user.day_
        time_t = calc_block_time(element["time"])
        due = calc_delta_t(time_t, day_offset)

        debug('QUEUE', 'next block in ' + str(due) + ' seconds. User: ' + str(user.chat_id_), log=True)
        new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
        user.job_ = new_job
        job_queue.put(new_job)
    return


# This function gets called at program start to load in
# all users from the DB. This function ensures that random
# crashes of the program are not an issue and no data loss occurs.
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
            user.age_ = row[2]
            user.country_ = row[3]
            user.gender_ = row[4]
            user.language_ = row[5]
            user.question_ = row[6]
            user.timezone_ = row[7]
            user.day_ = row[8]
            user.q_idle_ = row[9]
            user.active_ = row[10]
            user.block_ = row[11]
            user.pointer_ = row[12]
            user_map.participants[row[0]] = user

            if user.language_ != '':
                q_set = user_map.return_question_set_by_language(user.language_)
                user.q_set_ = q_set
                if user.pointer_ > 0:
                    user.set_next_block()
                    next_day = user.set_next_block()
                    element = user.next_block[2]  # Todo: Check if None!
                    day_offset = next_day - user.day_
                    time_t = calc_block_time(element["time"])
                    due = calc_delta_t(time_t, day_offset)

                    debug('QUEUE', 'next block in ' + str(due) + ' seconds. User: ' + str(user.chat_id_), log=True)
                    new_job = Job(queue_next, due, repeat=False, context=[user, job_queue])
                    job_queue.put(new_job)
            else:
                user.next_block = None
                if user.active_ and user.pointer_ > -1:
                    finished(user, job_queue)
    except sqlite3.Error as error:
        print(error)
    return user_map


