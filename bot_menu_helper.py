from typing import Dict
from telegram.ext import (
    ContextTypes,
)
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update,
)
import message_texts


def edit_product_inline_menu(product_id: int) -> InlineKeyboardMarkup:
    # Define the buttons of keyboard
    keyboard = [
        [
            InlineKeyboardButton("Edit", callback_data=f"edit__{product_id}"),
            InlineKeyboardButton("Remove", callback_data=f"remove__{product_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def edit_product_inline_sub_menu(product_id: int) -> InlineKeyboardMarkup:
    # Define the buttons of keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "Edit PROD/EXP date(s)",
                callback_data=f"edit_product_dates__{product_id}",
            ),
            InlineKeyboardButton(
                "Edit label photo", callback_data=f"edit_label__{product_id}"
            ),
        ],
        [InlineKeyboardButton("Cancel", callback_data=f"cancel__{product_id}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def main_menu():
    # Define the buttons of keyboard
    keyboard = [
        [KeyboardButton(message_texts.MYPROD_BUTTON_TEXT)],
        [KeyboardButton(message_texts.HELP_BUTTON_TEXT)],
    ]
    return ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True
    )  # , one_time_keyboard=True)


# Define the function to create the menu
async def init_main_menu(update: Update):
    if not update.message:
        raise ValueError("update.message is None")
    await update.message.reply_text("Press menu button...", reply_markup=main_menu())


# Define the function to add the menu to chat
async def add_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.chat_data, Dict):
        if "has_main_menu" not in context.chat_data or (
            "has_main_menu" in context.chat_data
            and not context.chat_data["has_main_menu"]
        ):
            await init_main_menu(update)
            context.chat_data["has_main_menu"] = True
