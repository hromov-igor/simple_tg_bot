from datetime import datetime
from os import getenv

from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.handlers_misc import (
    FILEINFO_WAITING_FILE,
    fileinfo_cancel,
    fileinfo_not_document,
    fileinfo_receive,
    fileinfo_start,
    help_cmd,
    rate_cmd,
    start_cmd,
    stats_cmd,
    weather_cmd,
)
from src.handlers_todo import todo_cmd, todo_pagination_cb
from src.logging_setup import setup_logging
from src.todo_service import TodoService

logger = setup_logging()


async def post_init(application: Application) -> None:
    todo_service = TodoService()
    await todo_service.init()
    application.bot_data["todo_service"] = todo_service
    application.bot_data["start_time"] = datetime.now()

    user_commands = [
        BotCommand("start", "Старт"),
        BotCommand("help", "Помощь"),
        BotCommand("todo", "Задачи"),
        BotCommand("stats", "Статистика"),
        BotCommand("weather", "Погода"),
        BotCommand("rate", "Курсы валют"),
        BotCommand("fileinfo", "Информация о файле"),
    ]

    await application.bot.set_my_commands(user_commands)
    await application.bot.set_chat_menu_button()


def main() -> None:

    load_dotenv()
    bot_token = getenv("BOT_TOKEN")

    application = Application.builder().token(bot_token).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("weather", weather_cmd))
    application.add_handler(CommandHandler("rate", rate_cmd))
    application.add_handler(CommandHandler("todo", todo_cmd))
    application.add_handler(CallbackQueryHandler(todo_pagination_cb, pattern=r"^todo:page:\d+$"))

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("fileinfo", fileinfo_start)],
        states={
            FILEINFO_WAITING_FILE: [
                MessageHandler(filters.Document.ALL, fileinfo_receive),
                MessageHandler(filters.COMMAND & ~filters.Regex(r'^/cancel'), fileinfo_not_document),
                MessageHandler(~filters.Document.ALL & ~filters.COMMAND, fileinfo_not_document),
            ]
        },
        fallbacks=[CommandHandler("cancel", fileinfo_cancel)],
    ))
    application.add_handler(CommandHandler("stats", stats_cmd))

    application.run_polling()


if __name__ == "__main__":
    main()
