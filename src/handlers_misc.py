import hashlib
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.services import CurrencyService, WeatherService
from src.stats import format_timedelta, parse_stats_from_logs

logger = logging.getLogger("simple_tg_bot")

FILEINFO_WAITING_FILE = 1


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот для работы с задачами, погодой и курсами валют. \nИспользуй /help для получения списка команд.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"STATS user_id={update.message.from_user.id} command=/help")
    await update.message.reply_text("""
/todo add <текст> - Добавить задачу
/todo list - Показать задачи
/todo done <id> - Отметить задачу выполненной
/weather <город> - Погода
/rate <базовая валюта> <валюта1,валюта2,...> - Курсы валют относительно одной базовой валюты
/fileinfo - Информация о файле (Имя, размер, SHA-256)
/stats - Статистика (аптайм, уникальные пользователи, число выполненных команд по типам, размер файла хранения в КБ)
/help - Эта команда
    """)


async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"STATS user_id={update.message.from_user.id} command=/weather args={context.args}")
    if not context.args:
        await update.message.reply_text("Использование: /weather <город>")
        return
    city = context.args[0]
    temp, description = await WeatherService.get_weather(city)
    if temp == -999:
        await update.message.reply_text(description)
    else:
        await update.message.reply_text(f"Погода в {city}: {temp}°C, {description}")


async def rate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"STATS user_id={update.message.from_user.id} command=/rate args={context.args}")
    if not context.args:
        await update.message.reply_text("Использование: /rate <базовая валюта> <валюта1,валюта2,...>")
        return
    base = context.args[0]
    symbols = context.args[1]
    rates = await CurrencyService.get_rates(base, symbols)
    if rates == [-1]:
        await update.message.reply_text("Не получилось получить курсы валют, попробуйте позже или измените валюты.")
    else:
        rates_str = "\n".join(rates)
        await update.message.reply_text(f"Курсы валют к {base}:\n{rates_str}")


async def fileinfo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"STATS user_id={update.message.from_user.id} command=/fileinfo")
    await update.message.reply_text("Пришлите файл для анализа.\nДля отмены — /cancel.")
    return FILEINFO_WAITING_FILE


async def fileinfo_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document

    try:
        tg_file = await document.get_file()
        data = await tg_file.download_as_bytearray()
        sha256_hash = hashlib.sha256(data).hexdigest()
        await update.message.reply_text(
            f"Имя файла: {document.file_name}\nРазмер: {document.file_size} байт\nSHA-256: {sha256_hash}"
        )
    except Exception:
        await update.message.reply_text("Не получилось обработать файл, попробуйте позже.")
    return ConversationHandler.END


async def fileinfo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


async def fileinfo_not_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Это не документ. Пожалуйста, пришлите файл. \nДля отмены — /cancel.")
    return FILEINFO_WAITING_FILE


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    start_time = context.bot_data["start_time"]
    uptime = datetime.now() - start_time
    user_ids, cmd_counter, total_bytes = parse_stats_from_logs("bot.log*")
    size_kb = total_bytes / 1024.0

    lines = [
        f"Аптайм: {format_timedelta(uptime)}",
        f"Уникальных пользователей: {len(user_ids)}",
        f"Размер логов: {size_kb:.2f} КБ",
        "",
    ]

    if cmd_counter:
        lines.append("Команды:")
        for cmd, cnt in cmd_counter.most_common(10):
            lines.append(f"/{cmd} — {cnt}")

    await update.message.reply_text("\n".join(lines))
