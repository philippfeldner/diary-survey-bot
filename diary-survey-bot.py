from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import TelegramError

from survey.keyboard_presets import languages

from survey.data_set import DataSet
from survey.questions import initialize_participants
from survey.questions import question_handler
from survey.questions import continue_survey
from survey.participant import Participant

from admin.settings import INFO_TEXT
from admin.settings import DEFAULT_LANGUAGE

data_set = None


def start(bot: Bot, update: Update, job_queue):
    global data_set
    if update.message.chat_id not in data_set.participants:
        reply_markup = ReplyKeyboardMarkup(languages)
        try:
            bot.send_message(chat_id=update.message.chat_id, text="Please choose a language:", reply_markup=reply_markup)
        except TelegramError as error:
            if error.message == 'Unauthorized':
                return
        participant = Participant(update.message.chat_id)
        data_set.participants[update.message.chat_id] = participant
    else:
        user = data_set.participants[update.message.chat_id]
        continue_survey(user, bot, job_queue)


def delete(bot: Bot, update: Update):
    global data_set
    chat_id = update.message.chat_id
    user = data_set.participants[update.message.chat_id]
    user.active_ = False
    user.delete_participant()
    del data_set.participants[update.message.chat_id]
    try:
        bot.send_message(chat_id=chat_id, text="Successfully deleted DB entry and user data. To restart enter /start")
    except TelegramError as error:
        if error.message == 'Unauthorized':
            user.pause()


def stop(bot: Bot, update: Update):
    global data_set
    chat_id = update.message.chat_id
    user = data_set.participants[update.message.chat_id]
    user.pause()
    try:
        bot.send_message(chat_id=chat_id, text="You have been set to inactive. If you want to continue enter /start")
    except TelegramError as error:
        if error.message == 'Unauthorized':
            user.pause()


def msg_handler(bot, update, job_queue):
    global data_set
    question_handler(bot, update, data_set, job_queue)
    

def info(bot: Bot, update: Update):
    global data_set
    try:
        user = data_set.participants[update.message.chat_id]
        message = INFO_TEXT[user.language_]
        try:
            bot.sendMessage(update.message.chat_id, text=message)
        except TelegramError:
            return
    except KeyError:
        message = INFO_TEXT[DEFAULT_LANGUAGE]
        try:
            bot.sendMessage(update.message.chat_id, text=message)
        except TelegramError:
            return


def main():
    updater = Updater("204036732:AAFFoO3Ew9D3nZ_gtXBGDXYpaHwPLn-oQb4")
    dp = updater.dispatcher
    global data_set
    data_set = initialize_participants(dp.job_queue)
    dp.add_handler(CommandHandler('start', start, pass_job_queue=True))
    dp.add_handler(CommandHandler('delete', delete))
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(MessageHandler(filters=[Filters.text], callback=msg_handler, pass_job_queue=True))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


