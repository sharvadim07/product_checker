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

from product_checker_bot import message_texts

PREFIX_EDIT_PRODUCT_DATES = "edit_product_dates"
PREFIX_EDIT_LABEL = "edit_label"
PREFIX_REMOVE = "remove"
PREFIX_CANCEL = "cancel"
PREFIX_EDIT = "edit"
PREFIX_DEL_PRODUCTS = "delete_products"
MAIN_MENU_FLAG = "has_main_menu"
YES_NO_MENU_FLAG = "has_yes_no_menu"


def edit_product_inline_menu(product_id: int) -> InlineKeyboardMarkup:
    # Define the buttons of keyboard
    keyboard = [
        [
            InlineKeyboardButton("Edit", callback_data=f"{PREFIX_EDIT}__{product_id}"),
            InlineKeyboardButton(
                "Remove", callback_data=f"{PREFIX_REMOVE}__{product_id}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def edit_product_inline_sub_menu(product_id: int) -> InlineKeyboardMarkup:
    # Define the buttons of keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "Edit PROD/EXP date(s)",
                callback_data=f"{PREFIX_EDIT_PRODUCT_DATES}__{product_id}",
            ),
            InlineKeyboardButton(
                "Edit label photo",
                callback_data=f"{PREFIX_EDIT_LABEL}__{product_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Cancel", callback_data=f"{PREFIX_CANCEL}__{product_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _main_menu():
    # Define the buttons of keyboard
    keyboard = [
        [KeyboardButton(message_texts.MYPROD_BUTTON)],
        [KeyboardButton(message_texts.DELETE_ALL_PRODUCTS_BUTTON)],
        [KeyboardButton(message_texts.HELP_BUTTON)],
    ]
    return ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True
    )  # , one_time_keyboard=True)


def _yes_no_menu():
    # Define the buttons of keyboard
    keyboard = [
        [KeyboardButton(message_texts.YES_BUTTON)],
        [KeyboardButton(message_texts.NO_BUTTON)],
    ]
    return ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True
    )  # , one_time_keyboard=True)


# Define the function to create the menu
async def _init_main_menu(update: Update):
    if not update.message:
        raise ValueError("update.message is None")
    await update.message.reply_text(
        message_texts.PRESS_MENU, reply_markup=_main_menu(), disable_notification=True
    )


async def _init_yes_no_menu(update: Update):
    if not update.message:
        raise ValueError("update.message is None")
    await update.message.reply_text(
        message_texts.ARE_YOU_SURE,
        reply_markup=_yes_no_menu(),
        disable_notification=True,
    )


# Define the function to add the menu to chat
async def add_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not isinstance(context.chat_data, Dict):
        raise ValueError("context.chat_data is None")
    await _init_main_menu(update)
    if YES_NO_MENU_FLAG in context.chat_data:
        context.chat_data[YES_NO_MENU_FLAG] = False
    context.chat_data[MAIN_MENU_FLAG] = True


async def add_yes_no_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not isinstance(context.chat_data, Dict):
        raise ValueError("context.chat_data is None")
    await _init_yes_no_menu(update)
    if MAIN_MENU_FLAG in context.chat_data:
        context.chat_data[MAIN_MENU_FLAG] = False
    context.chat_data[YES_NO_MENU_FLAG] = True
