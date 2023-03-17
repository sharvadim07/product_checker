from typing import Tuple, List
from telegram.ext import (
    ContextTypes,
)
from telegram import Update, CallbackQuery, error
from product_checker_bot import message_texts
from product_checker_bot.services.dates_recognition import check_text
from product_checker_bot.services.dates_recognition import get_prod_exp_dates
from product_checker_bot import db
from product_checker_bot.handlers import bot_menus
from product_checker_bot.handlers import help_


# Define the function to handle the button selection and text input
async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        raise ValueError("update.callback_query is None")
    if not update.message.text:
        raise ValueError("update.message.text is None")
    if update.message.text == message_texts.MYPROD_BUTTON_TEXT:
        await show_user_products(update, context)
    elif update.message.text == message_texts.HELP_BUTTON_TEXT:
        await help_(update, context)
    elif context.chat_data and bot_menus.PREFIX_EDIT_PRODUCT_DATES in context.chat_data:
        prod_to_edit = context.chat_data[bot_menus.PREFIX_EDIT_PRODUCT_DATES]
        try:
            await update_product_dates(prod_to_edit, update.message.text)
        except ValueError as e:
            await update.message.reply_text(message_texts.BAD_UPDATE_PRODUCT_DATES)
            raise ValueError(e)
        context.chat_data[bot_menus.PREFIX_EDIT_PRODUCT_DATES].pop()


async def show_user_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    bot_user = await db.get_add_bot_user(update.effective_user.id)
    if not bot_user.products:
        raise ValueError("bot_user.products is None")
    # Iterate other user products
    for cur_product in bot_user.products.values():
        if cur_product.label_path:
            # Download photo from Minio storage
            minio_photo = context.bot_data["my_minio"].get_object(
                object_name=message_texts.NAME_MINIO_OBJ.format(
                    telegram_user_id=bot_user.telegram_user_id,
                    product_id=cur_product.product_id,
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
                photo=minio_photo.data,
                disable_notification=True,
                reply_markup=bot_menus.edit_product_inline_menu(cur_product.product_id),
                caption=message_texts.PRODUCT_INFO.format(
                    product_id=cur_product.product_id,
                    date_prod=cur_product.date_prod,
                    date_exp=cur_product.date_exp,
                    label_path=cur_product.label_path,
                ),
            )


async def update_product_dates(
    prod_to_edit: List[Tuple[int, CallbackQuery]], text: str
):
    for product_id, query in prod_to_edit:
        prod_date, exp_date = get_prod_exp_dates(check_text(text, diff_years=100))
        if not (prod_date or exp_date):
            raise ValueError("Got bad dates from user.")
        cur_product = await db.get_product_db(product_id)
        if cur_product:
            await db.update_product(cur_product, prod_date=prod_date, exp_date=exp_date)
            if not query.message:
                raise ValueError("query.message is None")
            try:
                await query.message.edit_caption(
                    message_texts.PRODUCT_INFO.format(
                        product_id=cur_product.product_id,
                        date_prod=cur_product.date_prod,
                        date_exp=cur_product.date_exp,
                        label_path=cur_product.label_path,
                    ),
                    reply_markup=bot_menus.edit_product_inline_menu(product_id),
                )
            except error.BadRequest as e:
                raise ValueError(e)
