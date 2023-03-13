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
from config import config
from dates_recognition import dates_recognition
from dates_recognition import bytearray_to_img
from dates_recognition import get_prod_exp_dates
import entities
from minio_client import MyMinioClient

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

_NAME_MINIO_OBJ="user_{telegram_user_id}_product_{product_id}_photo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    if not update.effective_user:
        logging.error("update.effective_user is None")
        return
    try:
        await entities.get_add_bot_user(update.effective_user.id)
    except ValueError as e:
        logging.error(e)
        return
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
    if not update.effective_user:
        logging.error("update.effective_user is None")
        return
    try:
        # Get user and add new product
        bot_user = await entities.get_add_bot_user(update.effective_user.id)
        cur_product = await entities.new_user_product(bot_user)
        # Get uploaded by user photo
        photo = await update.message.photo[-1].get_file()
        downloaded_photo = await photo.download_as_bytearray()
        # Upoad photo of product to minio storage
        minio_res = context.bot_data["my_minio"].put_new_bytearray_photo(
            downloaded_photo, 
            str(bot_user.telegram_user_id),
            _NAME_MINIO_OBJ.format(
                telegram_user_id = bot_user.telegram_user_id, 
                product_id = cur_product.product_id
            )
        )
        # Update new product in DB
        await entities.update_product(
            cur_product,
            minio_res.object_name
        )
    except ValueError as e:
        logging.error(e)
        return
    # Get dates PROD/EXP
    prod_dates, exp_dates = get_prod_exp_dates(
        dates_recognition(
            bytearray_to_img(downloaded_photo),
            config.DATA_BOT_TEST_DIR
        )
    )
    try:
        # Update product in DB
        await entities.update_product(
            cur_product,
            minio_res.object_name,
            prod_dates,
            exp_dates
        )
    except ValueError as e:
        logging.error(e)
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message_texts.PRODUCT_INFO.format(
            product_id = cur_product.product_id,
            date_prod = cur_product.date_prod,
            date_exp = cur_product.date_exp,
            label_path = cur_product.label_path,
        )
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data["my_minio"] = MyMinioClient(config.MINIO_CREDENTIALS)
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    photo_handler = MessageHandler(filters.PHOTO, photo)
    application.add_handler(photo_handler)
    
    application.run_polling()