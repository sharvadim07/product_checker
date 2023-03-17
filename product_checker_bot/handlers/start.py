from telegram.ext import (
    ContextTypes,
)
from telegram import (
    Update,
)
from product_checker_bot.handlers import bot_menus
from product_checker_bot import db
from product_checker_bot import message_texts


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not update.message:
        raise ValueError("update.message is None")
    try:
        await db.get_add_bot_user(update.effective_user.id)
    except ValueError as e:
        raise ValueError(e)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_texts.GREETNGS.format(username=update.effective_user.username),
        disable_notification=True,
        parse_mode="html",
    )
    await bot_menus.add_main_menu(update, context)
