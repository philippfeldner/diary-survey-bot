try:
    # Get the user from the dict and its question_set (by language)
    user = user_map.participants[update.message.chat_id]  # type: Participant

    # Case for very first question.
    if user.question_ == -1:
        user.set_language(update.message)
        q_set = user_map.return_question_set_by_language(user.language_)
        question_id = user.set_question()
        q_current = q_set[question_id]
        user.set_day(1)
    # Case if the user was asked a question.
    elif user.q_idle_:
        q_set = user_map.return_question_set_by_language(user.language_)
        # Get the matching question for the users answer.
        q_prev = q_set[user.question_]
        if not valid_answer(q_prev, update.message):
            message = q_prev['question']
            reply_markup = get_keyboard(q_prev['choice'])
            bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=reply_markup)
            user.set_q_idle(True)
            return
        # Storing the answer and moving on the next question
        store_answer(user, update.message.text, q_prev)
        question_id = user.set_question()

        # Check if user has completed the whole survey
        if user.question_ == len(q_set):
            user.finished()
            # Todo: Send message and stuff

        q_current = q_set[question_id]
        user.set_q_idle(False)
    else:
        # User has send something without being asked a question.
        return
except KeyError as error:
    print(error)
    return

# Find next question for the user.
print(q_current['conditions_required'])
while not user.check_requirements(q_current['conditions_required']):
    question_id = user.set_question()
    q_current = q_set[question_id]

# Check if the new question is meant for another day.
if q_current['day'] != user.day_:
    user.day_complete_ = True

# If there is no auto_queue enabled and the user has answered all questions
# for the day a job for the next day gets scheduled.
if not user.auto_queue_ and user.day_complete_:
    user.set_day(q_current['day'])
    job = Job(queue_next, 5, repeat=False, context=[user, question_id, q_set, job_queue])
    job_queue.put(job)
    return

# No more questions for today
if user.day_complete_:
    user.set_day(q_current['day'])
    return

# Sending the new question
message = q_current['question']
q_keyboard = get_keyboard(q_current['choice'])
bot.send_message(chat_id=user.chat_id_, text=message, reply_markup=q_keyboard)
user.set_q_idle(True)