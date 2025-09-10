import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from todo_service import TodoService

logger = logging.getLogger("simple_tg_bot")


async def _build_todo_list_message(user_id: int, page: int, todo_service: TodoService):

    items, total = await todo_service.list_page(user_id, page, page_size=10)
    total_pages = max(1, (total // 10) + 1)
    lines = [f"Задачи {page}/{total_pages}:"]

    if not items:
        lines.append("Пока нет задач. Добавьте: /todo add <задача>")
    else:
        for t in items:
            status = "[+]" if t.done else "[]"
            lines.append(f"{t.id}. {status} {t.text}")

    keyboard = []
    nav = []

    if page > 1:
        nav.append(InlineKeyboardButton("Назад", callback_data="todo:page:"+str(page-1)))

    if page < total_pages:
        callback_data = "todo:page:"+str(page+1)
        nav.append(InlineKeyboardButton("Вперёд", callback_data=callback_data))
        logger.info(f"Created forward button with callback_data: {callback_data}")

    if nav:
        keyboard.append(nav)

    logger.info(f"Final keyboard: {[btn.callback_data for row in keyboard for btn in row] if keyboard else 'None'}")
    kb = InlineKeyboardMarkup(keyboard) if keyboard else None
    return "\n".join(lines), kb


async def todo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_id = update.message.from_user.id
    args = context.args
    todo_service = context.bot_data["todo_service"]

    if not args:
        await update.message.reply_text("Доступные команды:\n/todo list\n/todo add <текст>\n/todo done <id>")
        return

    sub = args[0].lower()

    if  sub == "list":
        logger.info(f"STATS user_id={user_id} command=/todo action=list")
        text, kb = await _build_todo_list_message(user_id, page=1, todo_service=todo_service)
        await update.message.reply_text(text, reply_markup=kb)
        return

    if sub == "add":
        logger.info(f"STATS user_id={user_id} command=/todo action=add")
        text = " ".join(args[1:])
        if not text:
            await update.message.reply_text("Использование: /todo add <задача>")
            return
        await todo_service.add(user_id, text)
        await update.message.reply_text("Добавлена задача: " + text)
        return

    if sub == "done":
        if len(args) < 2 or not args[1].isdigit():
            await update.message.reply_text("Использование: /todo done <id>")
            return
        result = await todo_service.mark_done(user_id, int(args[1]))
        logger.info(f"STATS user_id={user_id} command=/todo action=done id={args[1]} ok={result}")
        await update.message.reply_text("Готово." if result else "Задача не найдена.")
        return


async def todo_pagination_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    page = int(parts[-1])
    user_id = query.from_user.id

    todo_service = context.bot_data["todo_service"]
    text, kb = await _build_todo_list_message(user_id, page=page, todo_service=todo_service)

    await query.edit_message_text(text=text, reply_markup=kb)
