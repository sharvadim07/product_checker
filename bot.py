import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackQueryHandler

import message_texts
from config import config
from dates_recognition import dates_recognition
from dates_recognition import bytearray_to_img
from dates_recognition import get_prod_exp_dates
import entities
from minio_client import MyMinioClient
from PIL import Image
from io import BytesIO

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
    if not update.message:
        logging.error("update.message is None")
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
    await main_menu(update, context)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message_texts.HELP
    )
    await main_menu(update, context)

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
    
    await main_menu(update, context)

    # Get dates PROD/EXP
    prod_date, exp_date = get_prod_exp_dates(
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
            prod_date,
            exp_date
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

async def show_user_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        logging.error("update.effective_user is None")
        return
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    bot_user = await entities.get_add_bot_user(update.effective_user.id)
    if not bot_user.products:
        return
    # Iterate other user products
    for cur_product in bot_user.products.values():
        if cur_product.label_path:
            # Download photo from Minio storage
            minio_photo = context.bot_data["my_minio"].get_object(
                object_name = _NAME_MINIO_OBJ.format(
                    telegram_user_id = bot_user.telegram_user_id, 
                    product_id = cur_product.product_id
                )
            )
            # Resize image from minio
            # # create a BytesIO object to hold the byte stream
            # image_stream = BytesIO(minio_photo.data)
            # # open the image using the BytesIO object
            # image = Image.open(image_stream)
            # # resize the image
            # resized_image = image.resize((320, 320))
            # # save the resized image to a BytesIO object
            # output_stream = BytesIO()
            # resized_image.save(output_stream, format=image.format)
            # # get the byte representation of the resized image
            # resized_image_bytes = output_stream.getvalue()

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo = minio_photo.data,
                disable_notification = True,
                reply_markup = change_product_inline_menu(cur_product),
                caption = message_texts.PRODUCT_INFO.format(
                    product_id = cur_product.product_id,
                    date_prod = cur_product.date_prod,
                    date_exp = cur_product.date_exp,
                    label_path = cur_product.label_path,
                )
            )
            # await change_product_inline_menu(update, cur_product)
    await main_menu(update, context)
    
# Define the function to create the menu
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        logging.error("update.message is None")
        return
    buttons = [
        [KeyboardButton('My products')],
        [KeyboardButton('Help')]
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard = True, one_time_keyboard=True)
    await update.message.reply_text("Press menu button...", reply_markup = reply_markup)

# Define the function to handle the button selection
async def main_menu_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        logging.error("update.callback_query is None")
        return
    if update.message.text == 'My products':
        await show_user_products(update, context)
    elif update.message.text == 'Help':
       await help(update, context)

def change_product_inline_menu(
        cur_product : entities.Product
    ):
    # Define the buttons
    buttons = [
        InlineKeyboardButton(
            "Edit", 
            callback_data = \
                f"edit_{cur_product.product_id}"
        ),
        InlineKeyboardButton(
            "Remove", 
            callback_data = \
                f"remove_{cur_product.product_id}"
        )
    ]
    # Create the keyboard markup
    keyboard = [buttons]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup
    # Send the message with the menu
    # await update.message.reply_text("Yor action", reply_markup = reply_markup)

async def edit_product_inline_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        logging.error("query is None")
        return
    if not query.message:
        logging.error("update.message is None")
        return
    await query.answer()
    # Handle the selected option
    if str(query.data).startswith("edit"):
        pass
    elif str(query.data).startswith("remove"):
        await entities.remove_product_db(int(float(str(query.data).split('_')[1])))
        await query.message.delete()
        # await show_user_products(update, context)
    else:
        logging.warning("Unknown action!")
        return

# async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not update.message:
#         logging.error("update.message is None")
#         return
#     # Define the buttons
#     buttons = [
#         InlineKeyboardButton("Start", callback_data="start_option"),
#         InlineKeyboardButton("Help", callback_data="help_option"),
#         InlineKeyboardButton("My products", callback_data="my_products_option"),
#     ]
#     # Create the keyboard markup
#     keyboard = [buttons]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     # Send the message with the menu
#     await update.message.reply_text("Please choose an option:", reply_markup=reply_markup)

# async def menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     if not query:
#         logging.error("query is None")
#         return
#     await query.answer()
#     # Handle the selected option
#     if query.data == "start_option":
#         await start(update, context)
#     elif query.data == "help_option":
#         # Do something for option 2
#         await help(update, context)
#     elif query.data == "my_products_option":
#         # Do something for option 3
#         pass

if __name__ == '__main__':
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data["my_minio"] = MyMinioClient(config.MINIO_CREDENTIALS)
    
    # Add the handlers to the dispatcher
    application.add_handler(CommandHandler('menu', main_menu))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_button_callback))

    application.add_handler(CallbackQueryHandler(edit_product_inline_menu_callback))

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    listprod_handler = CommandHandler('listprod', show_user_products)
    application.add_handler(listprod_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    photo_handler = MessageHandler(filters.PHOTO, photo)
    application.add_handler(photo_handler)
    
    application.run_polling()