import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters
)
from io import BytesIO
from typing import Tuple, List
from datetime import date

import message_texts
from config import config
from dates_recognition import dates_recognition
from dates_recognition import bytearray_to_img
from dates_recognition import get_prod_exp_dates
import entities
import minio_client
from minio.api import ObjectWriteResult

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
    bot_user = await entities.get_bot_user(update.effective_user.id)
    if not bot_user:
        bot_user = await entities.add_new_bot_user(update.effective_user.id)
    if not bot_user:
        logging.error("bot_user is None")
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

async def get_bot_user_from_db(telegram_user_id : int) -> entities.BotUser:
    # Get user from DB
    bot_user = await entities.get_bot_user(telegram_user_id)
    if not bot_user:
        bot_user = await entities.add_new_bot_user(telegram_user_id)
    if not bot_user:
        logging.error("bot_user is None")
        raise ValueError
    return bot_user

async def new_product_of_user_db(bot_user : entities.BotUser) -> entities.Product:
    # Add new product to DB
    await entities.new_user_product(bot_user.telegram_user_id)
    # Get user with products
    updated_bot_user = await entities.get_bot_user(bot_user.telegram_user_id)
    if not updated_bot_user:
        logging.error("bot_user is None")
        raise ValueError
    if not updated_bot_user.products:
        logging.error("bot_user.products is None")
        raise ValueError
    bot_user.products = updated_bot_user.products
    return bot_user.products[list(bot_user.products.keys())[-1]]

async def update_product_db(
        cur_product : entities.Product,
        object_name : str,
        prod_dates : List[Tuple[str, date]],
        exp_dates : List[Tuple[str, date]]
    ) -> None:
    cur_product.label_path = object_name
    if len(prod_dates) > 0:
        cur_product.date_prod = prod_dates[-1][1].strftime("%d/%m/%Y")
    if len(exp_dates) > 0:
        cur_product.date_exp = exp_dates[0][1].strftime("%d/%m/%Y")
    await entities.update_product(
        cur_product.product_id,
        cur_product.label_path,
        cur_product.date_prod,
        cur_product.date_exp
    )

def upload_photo_minio(
        downloaded_photo : bytearray, 
        my_minio_client : minio_client.MyMinioClient,
        telegram_user_id : int,
        product_id : int
    ) -> ObjectWriteResult:
    # Upload photo ot Minio
    try:
        # Convert the bytearray to a bytes object
        data_bytes = bytes(downloaded_photo)
        # Create a BytesIO object to read the bytes
        data_stream = BytesIO(data_bytes)
        minio_res = my_minio_client.put_new_photo(
            data_stream, 
            len(data_bytes),
            str(telegram_user_id),
            f"user_{telegram_user_id}_product_{product_id}_photo"
        )
        return minio_res
    except (AttributeError, TypeError, ValueError):
        logging.error("Something goes wrong with minio")
        raise ValueError

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
    # Get user and add new product
    bot_user = await get_bot_user_from_db(update.effective_user.id)
    cur_product = await new_product_of_user_db(bot_user)
    # Get uploaded by user photo
    photo = await update.message.photo[-1].get_file()
    downloaded_photo = await photo.download_as_bytearray()
    minio_res = upload_photo_minio(
        downloaded_photo, 
        context.bot_data["my_minio"],
        bot_user.telegram_user_id,
        cur_product.product_id
    )
    # Get dates PROD/EXP
    prod_dates, exp_dates = get_prod_exp_dates(
        dates_recognition(
            bytearray_to_img(downloaded_photo),
            config.DATA_BOT_TEST_DIR
        )
    )
    # Update new product in DB
    await update_product_db(
        cur_product,
        minio_res.object_name,
        prod_dates,
        exp_dates
    )
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
    application.bot_data["my_minio"] = minio_client.MyMinioClient(config.MINIO_CREDENTIALS)
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    photo_handler = MessageHandler(filters.PHOTO, photo)
    application.add_handler(photo_handler)
    
    application.run_polling()