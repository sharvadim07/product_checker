import logging
from typing import Dict
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram import (
    Update,
)
import message_texts
from config import config
import entities
from minio_client import MyMinioClient
import bot_actions_helper
import bot_menu_helper
import bot_photo_helper

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


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
        text=message_texts.GREETNGS.format(username=update.effective_user.username),
    )
    await bot_menu_helper.add_main_menu(update, context)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        logging.error("update.effective_chat is None")
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=message_texts.HELP
    )
    # await main_menu(update)


async def photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data and bot_menu_helper.PREFIX_EDIT_LABEL in context.chat_data:
        try:
            await bot_photo_helper.edit_photo_label(update, context)
        except ValueError as e:
            logging.info(e)
    else:
        try:
            await bot_photo_helper.photo_simple_upload(update, context)
        except ValueError as e:
            logging.error(e)
            return
        await bot_menu_helper.add_main_menu(update, context)


# Define the function to handle the button selection and text input
async def text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        logging.error("update.callback_query is None")
        return
    if not update.message.text:
        logging.warning("update.message.text is None")
        return
    if update.message.text == message_texts.MYPROD_BUTTON_TEXT:
        await bot_actions_helper.show_user_products(update, context)
    elif update.message.text == message_texts.HELP_BUTTON_TEXT:
        await help(update, context)
    elif (
        context.chat_data
        and bot_menu_helper.PREFIX_EDIT_PRODUCT_DATES in context.chat_data
    ):
        prod_to_edit = context.chat_data[bot_menu_helper.PREFIX_EDIT_PRODUCT_DATES]
        try:
            await bot_actions_helper.update_product_dates(
                prod_to_edit, update.message.text
            )
        except ValueError as e:
            logging.info(e)
            await update.message.reply_text(message_texts.BAD_UPDATE_PRODUCT_DATES)
        context.chat_data[bot_menu_helper.PREFIX_EDIT_PRODUCT_DATES].pop()


async def product_inline_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if not query:
        logging.error("update.callback_query is None")
        return
    if not query.message:
        logging.error("update.message is None")
        return
    await query.answer()
    # Get product id from callback data
    product_id = int(float(str(query.data).split("__")[1]))
    # Handle the selected option
    if str(query.data).startswith(bot_menu_helper.PREFIX_EDIT_PRODUCT_DATES):
        await query.message.reply_text(message_texts.ENTER_PRODEXP_DATE)
        await query.edit_message_reply_markup(
            reply_markup=bot_menu_helper.edit_product_inline_menu(product_id)
        )
        if isinstance(context.chat_data, Dict):
            if bot_menu_helper.PREFIX_EDIT_PRODUCT_DATES not in context.chat_data:
                context.chat_data[bot_menu_helper.PREFIX_EDIT_PRODUCT_DATES] = [
                    (product_id, query)
                ]
            else:
                context.chat_data[bot_menu_helper.PREFIX_EDIT_PRODUCT_DATES].append(
                    (product_id, query)
                )
    elif str(query.data).startswith(bot_menu_helper.PREFIX_EDIT_LABEL):
        await query.message.reply_text(message_texts.SEND_NEW_LABEL_PHOTO)
        await query.edit_message_reply_markup(
            reply_markup=bot_menu_helper.edit_product_inline_menu(product_id)
        )
        if isinstance(context.chat_data, Dict):
            if bot_menu_helper.PREFIX_EDIT_LABEL not in context.chat_data:
                context.chat_data[bot_menu_helper.PREFIX_EDIT_LABEL] = [
                    (product_id, query)
                ]
            else:
                context.chat_data[bot_menu_helper.PREFIX_EDIT_LABEL].append(
                    (product_id, query)
                )
    elif str(query.data).startswith(bot_menu_helper.PREFIX_EDIT):
        await query.edit_message_reply_markup(
            reply_markup=bot_menu_helper.edit_product_inline_sub_menu(product_id)
        )
    elif str(query.data).startswith(bot_menu_helper.PREFIX_REMOVE):
        await entities.remove_product_db(product_id)
        await query.message.delete()
    elif str(query.data).startswith(bot_menu_helper.PREFIX_CANCEL):
        await query.edit_message_reply_markup(
            reply_markup=bot_menu_helper.edit_product_inline_menu(product_id)
        )
    else:
        logging.warning("Unknown action!")
        return


if __name__ == "__main__":
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data["my_minio"] = MyMinioClient(config.MINIO_CREDENTIALS)

    # Add the handlers to the dispatcher
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_callback)
    )
    application.add_handler(CallbackQueryHandler(product_inline_menu_callback))

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    photo_handler = MessageHandler(filters.PHOTO, photo_callback)
    application.add_handler(photo_handler)

    application.run_polling()
