from typing import Dict
from telegram.ext import (
    ContextTypes,
)
from telegram import (
    Update,
)

from product_checker_bot import message_texts
from product_checker_bot.handlers import bot_menus
from product_checker_bot import db


async def inline_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        raise ValueError("update.callback_query is None")
    if not query.message:
        raise ValueError("update.message is None")
    if not isinstance(context.chat_data, Dict):
        raise ValueError("context.chat_data is None")
    await query.answer()
    # Get product id from callback data
    product_id = int(float(str(query.data).split("__")[1]))
    # Handle the selected option
    if str(query.data).startswith(bot_menus.PREFIX_EDIT_PRODUCT_DATES):
        await query.message.reply_text(
            message_texts.ENTER_PRODEXP_DATE, disable_notification=True
        )
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_menu(product_id)
        )
        if bot_menus.PREFIX_EDIT_PRODUCT_DATES not in context.chat_data:
            context.chat_data[bot_menus.PREFIX_EDIT_PRODUCT_DATES] = [
                (product_id, query)
            ]
        else:
            context.chat_data[bot_menus.PREFIX_EDIT_PRODUCT_DATES].append(
                (product_id, query)
            )
    elif str(query.data).startswith(bot_menus.PREFIX_EDIT_LABEL):
        await query.message.reply_text(
            message_texts.SEND_NEW_LABEL_PHOTO, disable_notification=True
        )
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_menu(product_id)
        )
        if bot_menus.PREFIX_EDIT_LABEL not in context.chat_data:
            context.chat_data[bot_menus.PREFIX_EDIT_LABEL] = [(product_id, query)]
        else:
            context.chat_data[bot_menus.PREFIX_EDIT_LABEL].append((product_id, query))
    elif str(query.data).startswith(bot_menus.PREFIX_EDIT):
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_sub_menu(product_id)
        )
    elif str(query.data).startswith(bot_menus.PREFIX_REMOVE):
        await db.remove_product_db(product_id)
        await query.message.delete()
    elif str(query.data).startswith(bot_menus.PREFIX_CANCEL):
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_menu(product_id)
        )
