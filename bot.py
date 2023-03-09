import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters
)

import message_texts
import config
from dates_recognition import dates_recognition
from dates_recognition import bytearray_to_img
import entities

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    if not update.effective_user:
        logging.error("update.effective_user is None")
        return
    bot_user = await entities.get_add_bot_user(update.effective_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message_texts.GREETNGS.format(username = update.effective_user.username)
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message_texts.HELP
    )

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    if not update.message or not update.message.photo:
        logging.error("update.message is None")
        return
    photo = await update.message.photo[-1].get_file()
    downloaded_photo = await photo.download_as_bytearray()
    recognized_dates = dates_recognition(
        bytearray_to_img(downloaded_photo), config.DATA_BOT_TEST_DIR
    )
    if len(recognized_dates) > 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="PROD/EXP:\n" \
                + "\n".join([date_str for date_str in recognized_dates])
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="PROD/EXP dates not recognized :("
        )

if __name__ == '__main__':
    if not config.TELEGRAM_BOT_TOKEN:
        exit("Specify TELEGRAM_BOT_TOKEN variable!")

    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    photo_handler = MessageHandler(filters.PHOTO, photo)
    application.add_handler(photo_handler)
    
    application.run_polling()