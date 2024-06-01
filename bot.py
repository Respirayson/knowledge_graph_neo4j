import telegram
import logging
import os
from dotenv import load_dotenv
from time import sleep
from app import query_graph

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()

TOKEN = os.getenv("TOKEN")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
bot = telegram.Bot(token=TOKEN)

def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! Welcome to the Terrorism Bot, I am here to help give some basic information using my knowledge graph!')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    chat_id = update.message.chat.id
    bot.sendChatAction(chat_id=chat_id, action="typing")
    try:
        result = query_graph(update.message.text)
        answer = result["result"]
        if answer == "":
            answer = "Oops... Too violent and gemini has blocked me from answering..."
        update.message.reply_text(answer)
    except Exception as e:
        update.message.reply_text("Failed to process question. Please try again.")
        print(e)

def map(update, context):
    """Send a message when the command /map is issued."""
    update.message.reply_text('Map!')
    update.message.reply_location(37.4419, -122.1419)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def cancel(update, context):
    """Cancel the current action"""
    chat_id = update.message.chat.id
    bot.sendChatAction(chat_id=chat_id, action="typing")
    sleep(1.5)
    update.message.reply_text("Process cancelled!")
    return ConversationHandler.END




def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("map", map))
    

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()