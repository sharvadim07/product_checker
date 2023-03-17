import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

from product_checker_bot import handlers, config, services


def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Add minio client to application data
    application.bot_data["my_minio"] = services.MyMinioClient(config.MINIO_CREDENTIALS)

    # Add the handlers to the dispatcher
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message)
    )
    application.add_handler(CallbackQueryHandler(handlers.inline_menu_button))
    start_handler = CommandHandler("start", handlers.start)
    application.add_handler(start_handler)
    photo_handler = MessageHandler(filters.PHOTO, handlers.photo)
    application.add_handler(photo_handler)

    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        logging.warning(traceback.format_exc())
    finally:
        logging.info("Bot stopped.")
