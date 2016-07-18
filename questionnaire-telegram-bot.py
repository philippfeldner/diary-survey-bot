import time
import telegram
from participant import Participant
import questions
import threading
import admin
import sqlite3


participants = dict()


def initialize_participants():
    while 1:  # TODO as long as there are users stored in the DB
        participant_t = Participant(0)
        participants[3] = participant_t


# This function handles the
# user requests and works
# off all queued jobs
def message_handler(bot, update_id):
    for update in bot.getUpdates(offset=update_id, timeout=10):
        chat_id = update.message.chat_id
        update_id = update.update_id + 1
        message = update.message.text
        if chat_id in admin.settings.get_admins() and '/admin' in message:
            admin.control.handler(bot, message, chat_id)
        #elif '/start' in message:
            # Todo
        elif '/info' in message:
            reply = ' '
            bot.sendMessage(chat_id=chat_id, text=reply, parse_mode='HTML', disable_web_page_preview=True)
        else:
            participants[chat_id].response()
    return update_id


def main():
    bot = telegram.Bot(admin.control.get_bot_token('questionnaire.token'))
    # Todo: initialize Users and their time

    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None
    while True:
        try:
            # Todo call time checker function
            # function_1()
            update_id = message_handler(bot, update_id)
        except telegram.TelegramError as error:
            if error.message in ("Bad Gateway", "Timed out"):
                time.sleep(2)
            elif error.message == "Unauthorized":
                update_id += 1
            else:
                raise error

if __name__ == '__main__':
    main()


