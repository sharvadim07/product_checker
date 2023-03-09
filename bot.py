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
from dates_recognition import dates_recognition
from dates_recognition import bytearray_to_img

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN="6101847387:AAF7aVMaAN5wSu8SA-azotGZI7j1qGHt1MI"
DATA_BOT_TEST_DIR="data/bot_test"
#TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    exit("Specify TELEGRAM_BOT_TOKEN variable!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message_texts.GREETNGS
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
        bytearray_to_img(downloaded_photo), DATA_BOT_TEST_DIR
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
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    photo_handler = MessageHandler(filters.PHOTO, photo)
    application.add_handler(photo_handler)
    
    application.run_polling()