from telegram.ext import (
    ContextTypes,
)
from datetime import timedelta
from dateutil.parser import parse


from product_checker_bot import message_texts
from product_checker_bot.handlers import bot_menus
from product_checker_bot.db import Product, get_bot_users_and_products_db


async def _alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    product: Product = job.data
    if not context.bot_data["my_minio"]:
        raise ValueError("""context.bot_data["my_minio"] is None""")
    # Download photo from Minio storage
    minio_photo = context.bot_data["my_minio"].get_object(
        object_name=message_texts.NAME_MINIO_OBJ.format(
            telegram_user_id=job.user_id, product_id=product.product_id
        )
    )
    await context.bot.send_photo(
        chat_id=job.chat_id,
        photo=minio_photo.data,
        disable_notification=True,
        reply_markup=bot_menus.edit_product_inline_menu(product.product_id),
        caption=message_texts.PRODUCT_INFO_REMAIN_LIFE.format(
            remain_shelf_life_percent=product.remaining_shelf_life_percent(),
            product_id=product.product_id,
            date_prod=product.date_prod,
            date_exp=product.date_exp,
            label_path=product.label_path,
        ),
    )


def _check_alarm_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    else:
        return True


def _remove_alarm_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def _add_first_alarm(
    telegram_user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    product: Product,
    name: str,
    day_time_hour: int,
    remaining_shelf_life_percent: int,
):
    """Add first alarm which will be activated when threshold of remaining shelf life reached"""
    shelf_life_days = product.shelf_life_days()
    alarm_datetime = parse(product.date_exp) - timedelta(
        days=int(shelf_life_days * (remaining_shelf_life_percent / 100))
    )
    alarm_datetime = alarm_datetime.replace(
        hour=day_time_hour,
        minute=0,
        second=0,
    )
    # DEBUG
    # import random

    # alarm_datetime = timedelta(seconds=random.randint(10, 20))
    # Create notification by alarm
    context.job_queue.run_once(
        callback=_alarm,
        when=alarm_datetime,
        chat_id=telegram_user_id,
        user_id=telegram_user_id,
        name=name,
        data=product,
    )


def _add_second_alarm(
    telegram_user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    product: Product,
    name: str,
    day_time_hour: int,
    alarm_repeats_hours: int,
):
    """Add second alarm which will be activated when expiry date reached"""
    alarm_datetime = parse(product.date_exp).replace(
        hour=day_time_hour, minute=0, second=0
    )
    context.job_queue.run_repeating(
        callback=_alarm,
        interval=timedelta(hours=alarm_repeats_hours),
        first=alarm_datetime,
        chat_id=telegram_user_id,
        user_id=telegram_user_id,
        name=name,
        data=product,
    )


def update_product_alarm(
    context: ContextTypes.DEFAULT_TYPE,
    telegram_user_id: int,
    product: Product,
    remaining_shelf_life_percent: int = 30,
    day_time_hour: int = 3,
    alarm_repeats_hours: int = 24,
) -> None:
    """Update or create product expiry alarm.
    First alarm will at remaining shelf life day, second at the expiry day."""
    if not product.date_exp:
        return
    if not (0 < remaining_shelf_life_percent < 100):
        raise ValueError("Remaining shelf life should be between 0 and 100 %.")
    first_alarm_name = message_texts.NAME_ALARM.format(
        telegram_user_id=telegram_user_id, product_id=product.product_id, number=1
    )
    second_alarm_name = message_texts.NAME_ALARM.format(
        telegram_user_id=telegram_user_id, product_id=product.product_id, number=2
    )
    _remove_alarm_if_exists(first_alarm_name, context)
    _add_first_alarm(
        telegram_user_id,
        context,
        product,
        first_alarm_name,
        day_time_hour,
        remaining_shelf_life_percent,
    )
    _remove_alarm_if_exists(second_alarm_name, context)
    _add_second_alarm(
        telegram_user_id,
        context,
        product,
        second_alarm_name,
        day_time_hour,
        alarm_repeats_hours,
    )


def remove_product_alarm(
    context: ContextTypes.DEFAULT_TYPE,
    telegram_user_id: int,
    product_id: int,
) -> None:
    """Remove alarm for product"""
    first_alarm_name = message_texts.NAME_ALARM.format(
        telegram_user_id=telegram_user_id, product_id=product_id, number=1
    )
    second_alarm_name = message_texts.NAME_ALARM.format(
        telegram_user_id=telegram_user_id, product_id=product_id, number=2
    )
    _remove_alarm_if_exists(first_alarm_name, context)
    _remove_alarm_if_exists(second_alarm_name, context)


def init_all_alarms(context: ContextTypes.DEFAULT_TYPE):
    """Add alarms for all products of all users."""
    bot_users = get_bot_users_and_products_db()
    for bot_user in bot_users.values():
        if not bot_user.products:
            continue
        for product in bot_user.products.values():
            update_product_alarm(context, bot_user.telegram_user_id, product)