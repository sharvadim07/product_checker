from typing import Tuple, List
from telegram.ext import (
    ContextTypes, 
)
from telegram import (
    Update,
    CallbackQuery,
    error
)
import message_texts
from dates_recognition import check_text
from dates_recognition import get_prod_exp_dates
import entities
import bot_menu_helper

async def show_user_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    bot_user = await entities.get_add_bot_user(update.effective_user.id)
    if not bot_user.products:
        raise ValueError("bot_user.products is None")
    # Iterate other user products
    for cur_product in bot_user.products.values():
        if cur_product.label_path:
            # Download photo from Minio storage
            minio_photo = context.bot_data["my_minio"].get_object(
                object_name = message_texts._NAME_MINIO_OBJ.format(
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
                reply_markup = bot_menu_helper.edit_product_inline_menu(cur_product.product_id),
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
            try:
                await query.message.edit_caption(message_texts.PRODUCT_INFO.format(
                        product_id = cur_product.product_id,
                        date_prod = cur_product.date_prod,
                        date_exp = cur_product.date_exp,
                        label_path = cur_product.label_path
                    ),
                    reply_markup = bot_menu_helper.edit_product_inline_menu(product_id)
                )
            except error.BadRequest as e:
                raise ValueError(e)