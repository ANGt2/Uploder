import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN
from database import init_db
from handlers.user import (
    start,
    contact_handler,
    text_handler,
    photo_handler,
)
from handlers.admin import admin_panel
from handlers.callback import callback_handler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def main():
    print("Loading database...")
    init_db()

    print("Creating application...")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))

    app.add_handler(CallbackQueryHandler(callback_handler))

    app.add_handler(
        MessageHandler(filters.CONTACT, contact_handler)
    )

    app.add_handler(
        MessageHandler(filters.PHOTO, photo_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("====================================")
    print(" MixVoucher V4 Started Successfully ")
    print("====================================")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
