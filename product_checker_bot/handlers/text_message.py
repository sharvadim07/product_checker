from typing import Tuple, Dict
from telegram.ext import (
    ContextTypes,
)
from telegram import (
    Update,
    CallbackQuery,
    constants,
)
from product_checker_bot import message_texts
from product_checker_bot.services.dates_recognition import check_text
from product_checker_bot.services.dates_recognition import get_prod_exp_dates
from product_checker_bot import db
from product_checker_bot.handlers import bot_menus
from product_checker_bot.handlers import help_
from product_checker_bot import alarm


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function to handle the button selection and text input"""
    if not update.message:
        raise ValueError("update.callback_query is None")
    if not update.message.text:
        raise ValueError("update.message.text is None")
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
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
    if update.message.text == message_texts.MYPROD_BUTTON:
        try:
            await show_user_products(update, context)
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_texts.BAD_SHOW_PRODUCTS,
                disable_notification=True,
            )
    elif update.message.text == message_texts.HELP_BUTTON:
        await help_(update, context)
        await bot_menus.add_main_menu(update, context)
    elif bot_menus.PREFIX_EDIT_PRODUCT_DATES in context.chat_data:
        prod_to_edit = context.chat_data[bot_menus.PREFIX_EDIT_PRODUCT_DATES]
        try:
            await update_product_dates(prod_to_edit, update.message.text)
            product_id, _ = prod_to_edit
            # Update product alarm
            cur_product = await db.get_product_db(product_id)
            alarm.update_product_alarm(context, telegram_user_id, cur_product)
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_texts.BAD_UPDATE_PRODUCT_DATES,
                disable_notification=True,
            )
        finally:
            context.chat_data.pop(bot_menus.PREFIX_EDIT_PRODUCT_DATES)
    elif update.message.text == message_texts.DELETE_ALL_PRODUCTS_BUTTON:
        await bot_menus.add_yes_no_menu(update, context)
        context.chat_data[bot_menus.PREFIX_DEL_PRODUCTS] = True
    elif (
        bot_menus.PREFIX_DEL_PRODUCTS in context.chat_data
        and context.chat_data[bot_menus.PREFIX_DEL_PRODUCTS]
        and update.message.text == message_texts.YES_BUTTON
    ):
        try:
            await delete_all_user_products(update, context)
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_texts.BAD_DELETE_PRODUCT_DATES,
                disable_notification=True,
            )
        finally:
            await bot_menus.add_main_menu(update, context)
            context.chat_data[bot_menus.PREFIX_DEL_PRODUCTS] = False
    elif (
        bot_menus.PREFIX_DEL_PRODUCTS in context.chat_data
        and context.chat_data[bot_menus.PREFIX_DEL_PRODUCTS]
        and update.message.text == message_texts.NO_BUTTON
    ):
        await bot_menus.add_main_menu(update, context)
        context.chat_data[bot_menus.PREFIX_DEL_PRODUCTS] = False
    elif update.message.text != message_texts.PRESS_MENU:
        await bot_menus.add_main_menu(update, context)
    # Reset edit flags in context.chat_data when user send other query
    if bot_menus.PREFIX_EDIT_LABEL in context.chat_data:
        context.chat_data.pop(bot_menus.PREFIX_EDIT_LABEL)
    if bot_menus.PREFIX_EDIT_PRODUCT_DATES in context.chat_data:
        context.chat_data.pop(bot_menus.PREFIX_EDIT_PRODUCT_DATES)


async def delete_all_user_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Removing all user products from DB and remove linked alarms"""
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    # Set group chat as user if message send from it
    telegram_user_id = update.effective_user.id
    if update.effective_chat.type in (
        constants.ChatType.GROUP,
        constants.ChatType.SUPERGROUP,
    ):
        telegram_user_id = update.effective_chat.id
    bot_user = await db.get_add_bot_user(telegram_user_id)
    if not bot_user:
        raise ValueError("bot_user is None")
    if not bot_user.products:
        raise ValueError("bot_user.products is None")
    # Firstly remove alarms for these products
    for cur_product in bot_user.products.values():
        alarm.remove_product_alarm(
            context, bot_user.telegram_user_id, cur_product.product_id
        )
    await db.remove_all_products_db(telegram_user_id)


async def show_user_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of user products"""
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    # Set group chat as user if message send from it
    telegram_user_id = update.effective_user.id
    if update.effective_chat.type in (
        constants.ChatType.GROUP,
        constants.ChatType.SUPERGROUP,
    ):
        telegram_user_id = update.effective_chat.id
    bot_user = await db.get_add_bot_user(telegram_user_id)
    if not bot_user.products:
        raise ValueError("bot_user.products is None")
    # Iterate other user products
    for cur_product in bot_user.products.values():
        if cur_product.label_path:
            # Download photo from Minio storage
            minio_photo = context.bot_data["my_minio"].get_object(
                object_name=cur_product.label_path
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
                photo=minio_photo.data,
                disable_notification=True,
                reply_markup=bot_menus.edit_product_inline_menu(cur_product.product_id),
                caption=message_texts.PRODUCT_INFO_REMAIN_LIFE.format(
                    remain_shelf_life_percent=cur_product.remaining_shelf_life_percent(),
                    product_id=cur_product.product_id,
                    date_prod=cur_product.date_prod,
                    date_exp=cur_product.date_exp,
                    label_path=cur_product.label_path,
                ),
            )


async def update_product_dates(prod_to_edit: Tuple[int, CallbackQuery], text: str):
    """Update dates of production and expiration"""
    product_id, query = prod_to_edit
    prod_date, exp_date = get_prod_exp_dates(check_text(text, diff_years=100))
    if not (prod_date or exp_date):
        raise ValueError("Got bad dates from user.")
    cur_product = await db.get_product_db(product_id)
    if cur_product:
        cur_product = await db.update_product(
            product_id=cur_product.product_id,
            prod_date=prod_date,
            exp_date=exp_date,
        )
        if not query.message:
            raise ValueError("query.message is None")
        new_text = message_texts.PRODUCT_INFO_REMAIN_LIFE.format(
            remain_shelf_life_percent=cur_product.remaining_shelf_life_percent(),
            product_id=cur_product.product_id,
            date_prod=cur_product.date_prod,
            date_exp=cur_product.date_exp,
            label_path=cur_product.label_path,
        )
        if new_text != query.message.caption:
            await query.message.edit_caption(
                new_text,
                reply_markup=bot_menus.edit_product_inline_menu(product_id),
            )
