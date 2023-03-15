import logging
from typing import Optional, Dict, Tuple, List
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters
)
from telegram import (
    Update,
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    CallbackQuery,
    Message,
    InputMediaPhoto
)
import message_texts
from config import config
from dates_recognition import dates_recognition
from dates_recognition import check_text
from dates_recognition import bytearray_to_img
from dates_recognition import get_prod_exp_dates
import entities
from minio_client import MyMinioClient
from minio.api import ObjectWriteResult
from io import BytesIO
# from PIL import Image
# from io import BytesIO

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
    await main_menu(update)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message_texts.HELP
    )
    await main_menu(update)

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data and "edit_label" in context.chat_data:
        try:
            await edit_photo_label(update, context)
        except ValueError as e:
            logging.info(e)
    else:
        try:
            await photo_simple_upload(update, context)
        except ValueError as e:
            logging.error(e)
            return
    await main_menu(update)

async def photo_label_update(
        update : Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        telegram_user_id : int, 
        product_id : int
    ) -> Tuple[ObjectWriteResult, bytearray]:
    if not update.message or not update.message.photo:
        raise ValueError("update.message is None")
    # Get uploaded by user photo
    photo = await update.message.photo[-1].get_file()
    downloaded_photo = await photo.download_as_bytearray()
    # Upoad photo of product to minio storage
    minio_res = context.bot_data["my_minio"].put_new_bytearray_photo(
        downloaded_photo, 
        str(telegram_user_id),
        _NAME_MINIO_OBJ.format(
            telegram_user_id = telegram_user_id, 
            product_id = product_id
        )
    )
    return minio_res, downloaded_photo

async def replace_user_photo(
        update : Update, 
        context : ContextTypes.DEFAULT_TYPE,
        downloaded_photo : bytearray,
        cur_product : entities.Product
    ) -> Message:
    if not update.message:
        raise ValueError("update.message is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    # Firstly delete user message wiht photo
    await update.message.delete()
    # Convert the bytearray to a bytes object
    data_bytes = bytes(downloaded_photo)
    # Create a BytesIO object to read the bytes
    data_stream = BytesIO(data_bytes)
    product_message = await context.bot.send_photo(
        chat_id = update.effective_chat.id,
        photo = data_stream,
        disable_notification = True,
        reply_markup = edit_product_inline_menu(cur_product.product_id),
        caption = message_texts.PRODUCT_INFO.format(
            product_id = cur_product.product_id,
            date_prod = cur_product.date_prod,
            date_exp = cur_product.date_exp,
            label_path = cur_product.label_path,
        )
    )
    return product_message

async def photo_simple_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    if not update.message:
        raise ValueError("update.message is None")
    # Get user and add new product
    bot_user = await entities.get_add_bot_user(update.effective_user.id)
    cur_product = await entities.new_user_product(bot_user)
    minio_res, downloaded_photo = await photo_label_update(
        update = update,
        context = context,
        telegram_user_id = bot_user.telegram_user_id,
        product_id = cur_product.product_id
    )
    # Update product in DB
    await entities.update_product(
        cur_product = cur_product,
        label_path = minio_res.object_name
    )
    # Replace user photo to mesage with product info
    product_message = await replace_user_photo(
                update = update,
                context = context,
                downloaded_photo = downloaded_photo,
                cur_product = cur_product
            )
    # Get dates PROD/EXP
    prod_date, exp_date = get_prod_exp_dates(
        dates_recognition(
            bytearray_to_img(downloaded_photo),
            config.DATA_BOT_TEST_DIR
        )
    )
    if prod_date or exp_date:
        # Update product in DB
        await entities.update_product(
            cur_product = cur_product,
            prod_date = prod_date,
            exp_date = exp_date
        )
        # Update product caption
        await product_message.edit_caption(
            caption = message_texts.PRODUCT_INFO.format(
                product_id = cur_product.product_id,
                date_prod = cur_product.date_prod,
                date_exp = cur_product.date_exp,
                label_path = cur_product.label_path,
            ),
            reply_markup = edit_product_inline_menu(cur_product.product_id)
        )

async def edit_photo_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not (context.chat_data and "edit_label" in context.chat_data):
        raise ValueError("context.chat_data is None")
    if not update.message:
        raise ValueError("update.message is None")
    prod_to_edit = context.chat_data["edit_label"]
    for product_id, query in prod_to_edit:
        # Get user
        bot_user = await entities.get_add_bot_user(update.effective_user.id)
        cur_product = await entities.get_product_db(product_id)
        if not cur_product:
            raise ValueError("cur_product is None")
        minio_res, downloaded_photo = await photo_label_update(
            update = update,
            context = context,
            telegram_user_id = bot_user.telegram_user_id,
            product_id = cur_product.product_id
        )
        # Update new product in DB
        await entities.update_product(
            cur_product = cur_product,
            label_path = minio_res.object_name
        )
        if not query.message:
            raise ValueError("query.message is None")
        await update.message.delete()
        await query.message.edit_media(InputMediaPhoto(bytes(downloaded_photo)))
        # Update product caption
        await query.message.edit_caption(
            caption = message_texts.PRODUCT_INFO.format(
                product_id = cur_product.product_id,
                date_prod = cur_product.date_prod,
                date_exp = cur_product.date_exp,
                label_path = cur_product.label_path,
            ),
            reply_markup = edit_product_inline_menu(cur_product.product_id)
        )
    context.chat_data["edit_label"].pop()

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
                reply_markup = edit_product_inline_menu(cur_product.product_id),
                caption = message_texts.PRODUCT_INFO.format(
                    product_id = cur_product.product_id,
                    date_prod = cur_product.date_prod,
                    date_exp = cur_product.date_exp,
                    label_path = cur_product.label_path,
                )
            )
            # await edit_product_inline_menu(update, cur_product)
    # await main_menu(update)
    
async def update_product_dates(prod_to_edit : List[Tuple[int, CallbackQuery]], text : str):
    for product_id, query in prod_to_edit:
        prod_date, exp_date = get_prod_exp_dates(
            check_text(text, diff_years = 100)
        )
        if not (prod_date or exp_date):
            raise ValueError("Got bad dates from user.")
        cur_product = await entities.get_product_db(product_id)
        if cur_product:
            await entities.update_product(
                cur_product,
                prod_date = prod_date,
                exp_date = exp_date
            )
            if not query.message:
                raise ValueError("query.message is None")
            await query.message.edit_caption(message_texts.PRODUCT_INFO.format(
                    product_id = cur_product.product_id,
                    date_prod = cur_product.date_prod,
                    date_exp = cur_product.date_exp,
                    label_path = cur_product.label_path
                ),
                reply_markup = edit_product_inline_menu(product_id)
            )

# Define the function to create the menu
async def main_menu(update: Update):
    if not update.message:
        logging.error("update.message is None")
        return
    buttons = [
        [KeyboardButton(message_texts.MYPROD_BUTTON_TEXT)],
        [KeyboardButton(message_texts.HELP_BUTTON_TEXT)]
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard = True) #, one_time_keyboard=True)
    await update.message.reply_text("Press menu button...", reply_markup = reply_markup)

# Define the function to handle the button selection
async def main_menu_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        logging.error("update.callback_query is None")
        return
    if not update.message.text:
        logging.warning("update.message.text is None")
        return
    if update.message.text == message_texts.MYPROD_BUTTON_TEXT:
        await show_user_products(update, context)
    elif update.message.text == message_texts.HELP_BUTTON_TEXT:
       await help(update, context)
    elif context.chat_data and "edit_product_dates" in context.chat_data:
        prod_to_edit = context.chat_data["edit_product_dates"]
        try:
            await update_product_dates(prod_to_edit, update.message.text)
        except ValueError as e:
            logging.info(e)
            await update.message.reply_text("Bad dates. Please retry to edit product...")
        context.chat_data["edit_product_dates"].pop()

def edit_product_inline_menu(
        product_id : int
    ) -> InlineKeyboardMarkup:
    # Define the buttons
    buttons = [
        InlineKeyboardButton(
            "Edit", 
            callback_data = \
                f"edit__{product_id}"
        ),
        InlineKeyboardButton(
            "Remove", 
            callback_data = \
                f"remove__{product_id}"
        )
    ]
    # Create the keyboard markup
    keyboard = [buttons]
    return InlineKeyboardMarkup(keyboard)
    # Send the message with the menu
    # await update.message.reply_text("Yor action", reply_markup = reply_markup)

def edit_product_inline_sub_menu(
        product_id : int
    ) -> InlineKeyboardMarkup:
    # Define the buttons
    buttons = [
        InlineKeyboardButton(
            "Edit PROD/EXP date(s)", 
            callback_data = \
                f"edit_product_dates__{product_id}"
        ),
        InlineKeyboardButton(
            "Edit label photo", 
            callback_data = \
                f"edit_label__{product_id}"
        )
    ]
    # Create the keyboard markup
    keyboard = [buttons]
    return InlineKeyboardMarkup(keyboard)

async def edit_product_inline_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        logging.error("query is None")
        return
    if not query.message:
        logging.error("update.message is None")
        return
    await query.answer()
    product_id = int(float(str(query.data).split('__')[1]))
    # Handle the selected option
    if str(query.data).startswith("edit_product_dates"):
        await query.message.reply_text(message_texts.ENTER_PRODEXP_DATE)
        await query.edit_message_reply_markup(reply_markup = edit_product_inline_menu(product_id))
        if isinstance(context.chat_data, Dict):
            if "edit_product_dates" not in context.chat_data:
                context.chat_data["edit_product_dates"] = [(product_id, query)]
            else:
                context.chat_data["edit_product_dates"].append((product_id, query))
    elif str(query.data).startswith("edit_label"):
        await query.message.reply_text(message_texts.SEND_NEW_LABEL_PHOTO)
        await query.edit_message_reply_markup(reply_markup = edit_product_inline_menu(product_id))
        if isinstance(context.chat_data, Dict):
            if "edit_label" not in context.chat_data:
                context.chat_data["edit_label"] = [(product_id, query)]
            else:
                context.chat_data["edit_label"].append((product_id, query))
    elif str(query.data).startswith("edit"):
        await query.edit_message_reply_markup(reply_markup = edit_product_inline_sub_menu(product_id))
    elif str(query.data).startswith("remove"):
        await entities.remove_product_db(product_id)
        await query.message.delete()
    else:
        logging.warning("Unknown action!")
        return

if __name__ == '__main__':
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data["my_minio"] = MyMinioClient(config.MINIO_CREDENTIALS)
    
    # Add the handlers to the dispatcher
    # application.add_handler(CommandHandler('menu', main_menu))
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