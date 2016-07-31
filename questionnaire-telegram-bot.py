from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from survey.keyboard_presets import smiley_scale_5
from survey.keyboard_presets import languages

from survey.participant import DataSet
from survey.participant import initialize_participants
from survey.questions import question_handler
from survey.participant import Participant

data_set = None


def start(bot: Bot, update: Update):
    global data_set
    if update.message.chat_id not in data_set.participants:
        reply_markup = ReplyKeyboardMarkup(languages)
        bot.send_message(chat_id=update.message.chat_id, text="Please choose a language:", reply_markup=reply_markup)
        participant = Participant(update.message.chat_id)
        data_set.participants[update.message.chat_id] = participant


def stop(bot: Bot, update: Update):
    global data_set
    chat_id = update.message.chat_id
    user = data_set.participants[update.message.chat_id]
    user.delete_participant()
    del data_set.participants[update.message.chat_id]
    # Message for /stop
    bot.send_message(chat_id=chat_id, text="Test")


def msg_handler(bot, update, job_queue):
    global data_set
    question_handler(bot, update, data_set, job_queue)
    

def info(bot: Bot, update: Update):
    # Message for /info
    bot.sendMessage(update.message.chat_id, text='')


def main():
    updater = Updater("204036732:AAFFoO3Ew9D3nZ_gtXBGDXYpaHwPLn-oQb4")
    dp = updater.dispatcher
    global data_set
    data_set = initialize_participants(dp.job_queue)  # type: DataSet
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(MessageHandler(filters=[Filters.text], callback=msg_handler, pass_job_queue=True))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


