from telegram.ext import (
    ContextTypes,
)
from telegram import (
    Update,
)

from product_checker_bot import message_texts


async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_texts.HELP,
        disable_notification=True,
    )
