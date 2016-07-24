#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to send timed Telegram messages
# This program is dedicated to the public domain under the CC0 license.


from telegram.ext import Updater, CommandHandler, Job, ConversationHandler, MessageHandler
from telegram import Bot, Update
import users.participant as participant
from users import Participant
import logging
from data import question_handler
import admin.settings as settings


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def start(bot: Bot, update: Update):
    bot.send_message()
    Participant(update.message.chat_id)


def stop(bot: Bot, update: Update):
    bot.send_message()
    user = participant.dict_p[update.message.chat_id]
    user.delete_participant()  # type: Participant


def info(bot: Bot, update: Update):
    bot.sendMessage(update.message.chat_id, text='INFO PLACEHOLDER')


def handler(bot, update):
    message = question_handler()


def main():
    updater = Updater("TOKEN")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(MessageHandler())

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()


