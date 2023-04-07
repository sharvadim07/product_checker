from typing import Dict
from telegram.ext import (
    ContextTypes,
)
from telegram import (
    Update,
    constants,
)

from product_checker_bot import message_texts
from product_checker_bot.handlers import bot_menus
from product_checker_bot import db
from product_checker_bot import alarm


async def inline_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        raise ValueError("update.callback_query is None")
    if not query.message:
        raise ValueError("update.message is None")
    if not isinstance(context.chat_data, Dict):
        raise ValueError("context.chat_data is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    # Set group chat as user if message send from it
    telegram_user_id = update.effective_user.id
    if update.effective_chat.type in (
        constants.ChatType.GROUP,
        constants.ChatType.SUPERGROUP,
    ):
        telegram_user_id = update.effective_chat.id
    await query.answer()
    # Get product id from callback data
    product_id = int(float(str(query.data).split("__")[1]))
    # Handle the selected option
    if str(query.data).startswith(bot_menus.PREFIX_EDIT_PRODUCT_DATES):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_texts.ENTER_PRODEXP_DATE,
            disable_notification=True,
        )
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_menu(product_id)
        )
        context.chat_data[bot_menus.PREFIX_EDIT_PRODUCT_DATES] = (product_id, query)
    elif str(query.data).startswith(bot_menus.PREFIX_EDIT_LABEL):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_texts.SEND_NEW_LABEL_PHOTO,
            disable_notification=True,
        )
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_menu(product_id)
        )
        context.chat_data[bot_menus.PREFIX_EDIT_LABEL] = (product_id, query)
    elif str(query.data).startswith(bot_menus.PREFIX_EDIT):
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_sub_menu(product_id)
        )
    elif str(query.data).startswith(bot_menus.PREFIX_REMOVE):
        await db.remove_product_db(product_id)
        alarm.remove_product_alarm(context, telegram_user_id, product_id)
        await query.message.delete()
    elif str(query.data).startswith(bot_menus.PREFIX_CANCEL):
        await query.edit_message_reply_markup(
            reply_markup=bot_menus.edit_product_inline_menu(product_id)
        )
