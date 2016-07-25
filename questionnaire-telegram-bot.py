from telegram.ext import Updater, CommandHandler, Job, MessageHandler, Filters
from telegram import Bot, Update
from user import Participant
from data.questions import question_handler
from user.participant import User
import sqlite3

user_map = User()


def start(bot: Bot, update: Update):
    global user_map
    if update.message.chat_id not in user_map.participants:
        participant = Participant(update.message.chat_id)
        user_map.participants[update.message.chat_id] = participant
    # Message for /start
    bot.send_message(chat_id=update.message.chat_id, text="Test")


def stop(bot: Bot, update: Update):
    global user_map
    chat_id = update.message.chat_id
    user = user_map.participants[update.message.chat_id]
    user.delete_participant()
    del user_map.participants[update.message.chat_id]
    # Message for /stop
    bot.send_message(chat_id=chat_id, text="Test")


def msg_handler(bot, update):
    global user_map
    user = user_map.participants[update.message.chat_id]
    question_handler(bot, update, user)
    

def info(bot: Bot, update: Update):
    # Message for /info
    bot.sendMessage(update.message.chat_id, text='')


def main():
    updater = Updater("204036732:AAFFoO3Ew9D3nZ_gtXBGDXYpaHwPLn-oQb4")
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(MessageHandler(filters=[Filters.text], callback=msg_handler, pass_job_queue=True))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


