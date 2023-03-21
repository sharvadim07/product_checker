from typing import Tuple, Dict
from minio.api import ObjectWriteResult
from io import BytesIO

from telegram.ext import (
    ContextTypes,
)
from telegram import (
    Update,
    Message,
    InputMediaPhoto,
)

from product_checker_bot import message_texts
from config import config
from product_checker_bot.services.dates_recognition import dates_recognition
from product_checker_bot.services.dates_recognition import bytearray_to_img
from product_checker_bot.services.dates_recognition import get_prod_exp_dates
from product_checker_bot.handlers import bot_menus
from product_checker_bot import db
from product_checker_bot import alarm


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler of photo messages"""
    if not update.message:
        raise ValueError("update.message is None")
    if not isinstance(context.chat_data, Dict):
        raise ValueError("context.chat_data is None")
    if bot_menus.PREFIX_EDIT_LABEL in context.chat_data:
        try:
            await edit_photo_label(update, context)
        except ValueError:
            await update.message.reply_text(
                message_texts.BAD_PHOTO_UPLOAD, disable_notification=True
            )
        finally:
            context.chat_data.pop(bot_menus.PREFIX_EDIT_LABEL)
    else:
        try:
            await photo_simple_upload(update, context)
        except ValueError:
            await update.message.reply_text(
                message_texts.BAD_PHOTO_UPLOAD, disable_notification=True
            )
    if bot_menus.MAIN_MENU_FLAG not in context.chat_data:
        await bot_menus.add_main_menu(update, context)


async def photo_label_update(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_user_id: int,
    product_id: int,
) -> Tuple[ObjectWriteResult, bytearray]:
    """Set new photo label of product"""
    if not update.message or not update.message.photo:
        raise ValueError("update.message is None")
    # Get uploaded by user photo
    photo = await update.message.photo[-1].get_file()
    downloaded_photo = await photo.download_as_bytearray()
    # Upoad photo of product to minio storage
    minio_res = context.bot_data["my_minio"].put_new_bytearray_photo(
        downloaded_photo,
        str(telegram_user_id),
        message_texts.NAME_MINIO_OBJ.format(
            telegram_user_id=telegram_user_id, product_id=product_id
        ),
    )
    return minio_res, downloaded_photo


async def replace_user_product_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    downloaded_photo: bytearray,
    cur_product: db.Product,
) -> Message:
    """Function for handle when user send photo to change photo label of existed product"""
    if not update.message:
        raise ValueError("update.message is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    # Firstly delete user message wiht photo
    await update.message.delete()
    # Convert the bytearray to a bytes object
    data_bytes = bytes(downloaded_photo)
    # Create a BytesIO object to read the bytes
    data_stream = BytesIO(data_bytes)
    product_message = await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=data_stream,
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
    return product_message


async def photo_simple_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle action when user sends photo"""
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not update.effective_chat:
        raise ValueError("update.effective_chat is None")
    if not update.message:
        raise ValueError("update.message is None")
    # Get user and add new product
    cur_product, bot_user = await db.new_user_product(update.effective_user.id)
    minio_res, downloaded_photo = await photo_label_update(
        update=update,
        context=context,
        telegram_user_id=bot_user.telegram_user_id,
        product_id=cur_product.product_id,
    )
    # Update product in DB
    cur_product = await db.update_product(
        product_id=cur_product.product_id, label_path=minio_res.object_name
    )
    # Replace user photo to mesage with product info
    product_message = await replace_user_product_photo(
        update=update,
        context=context,
        downloaded_photo=downloaded_photo,
        cur_product=cur_product,
    )
    # Get dates PROD/EXP
    prod_date, exp_date = get_prod_exp_dates(
        dates_recognition(bytearray_to_img(downloaded_photo), config.DATA_BOT_TEST_DIR)
    )
    if prod_date or exp_date:
        # Update product in DB
        cur_product = await db.update_product(
            product_id=cur_product.product_id, prod_date=prod_date, exp_date=exp_date
        )
        # Update product alarm
        alarm.update_product_alarm(context, bot_user.telegram_user_id, cur_product)
        # Update product caption
        await product_message.edit_caption(
            caption=message_texts.PRODUCT_INFO_REMAIN_LIFE.format(
                remain_shelf_life_percent=cur_product.remaining_shelf_life_percent(),
                product_id=cur_product.product_id,
                date_prod=cur_product.date_prod,
                date_exp=cur_product.date_exp,
                label_path=cur_product.label_path,
            ),
            reply_markup=bot_menus.edit_product_inline_menu(cur_product.product_id),
        )


async def edit_photo_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for action when user select edit photo label in inline menu"""
    if not update.effective_user:
        raise ValueError("update.effective_user is None")
    if not (context.chat_data and bot_menus.PREFIX_EDIT_LABEL in context.chat_data):
        raise ValueError("context.chat_data is None")
    if not update.message:
        raise ValueError("update.message is None")
    prod_to_edit = context.chat_data[bot_menus.PREFIX_EDIT_LABEL]
    product_id, query = prod_to_edit
    # Get user
    bot_user = await db.get_add_bot_user(update.effective_user.id)
    cur_product = await db.get_product_db(product_id)
    if not cur_product:
        raise ValueError("cur_product is None")
    minio_res, downloaded_photo = await photo_label_update(
        update=update,
        context=context,
        telegram_user_id=bot_user.telegram_user_id,
        product_id=cur_product.product_id,
    )
    # Update new product in DB
    cur_product = await db.update_product(
        product_id=cur_product.product_id, label_path=minio_res.object_name
    )
    if not query.message:
        raise ValueError("query.message is None")
    await update.message.delete()
    await query.message.edit_media(InputMediaPhoto(bytes(downloaded_photo)))
    # Update product caption
    await query.message.edit_caption(
        caption=message_texts.PRODUCT_INFO_REMAIN_LIFE.format(
            remain_shelf_life_percent=cur_product.remaining_shelf_life_percent(),
            product_id=cur_product.product_id,
            date_prod=cur_product.date_prod,
            date_exp=cur_product.date_exp,
            label_path=cur_product.label_path,
        ),
        reply_markup=bot_menus.edit_product_inline_menu(cur_product.product_id),
    )
