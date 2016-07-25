from telegram.ext import Updater, CommandHandler, Job, MessageHandler, Filters
from telegram import Bot, Update
import users.participant as participant
from users import Participant
from data.questions import question_handler


def start(bot: Bot, update: Update):
    bot.send_message(chat_id=update.message.chat_id, text="Test")
    if update.message.chat_id not in participant.dict_p:
        Participant(update.message.chat_id)


def stop(bot: Bot, update: Update):
    bot.send_message(chat_id=update.message.chat_id, text="Test")
    user = participant.dict_p[update.message.chat_id]
    user.delete_participant()  # type: Participant


def info(bot: Bot, update: Update):
    bot.sendMessage(update.message.chat_id, text='')


def main():
    updater = Updater("204036732:AAFFoO3Ew9D3nZ_gtXBGDXYpaHwPLn-oQb4")
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(MessageHandler(filters=[Filters.text], callback=question_handler, pass_job_queue=True))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


