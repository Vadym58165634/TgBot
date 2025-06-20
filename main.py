from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from telegram.constants import ChatMemberStatus
from datetime import timedelta
import re

TOKEN = os.getenv("BOT_TOKEN")  # токен будет задаваться через переменную среды
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
MENU = range(1)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 Управление чатом", callback_data='chat')],
        [InlineKeyboardButton("ℹ Информация", callback_data='info')],
        [InlineKeyboardButton("📞 Поддержка", callback_data='support')],
        [InlineKeyboardButton("⚙ Админ-панель", callback_data='admin')]
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Назад", callback_data='back')]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if chat.type in ['group', 'supergroup']:
        await update.message.reply_text("✅ Бот активен в этой группе.")
        return MENU

    await update.message.reply_text(
        f"Привет, {user.first_name}! Добро пожаловать в Emerald ModularBot.\nВыберите модуль:",
        reply_markup=main_menu()
    )
    return MENU

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'chat':
        await query.edit_message_text("Модуль управления чатом:\nКоманды: /ban /mute", reply_markup=back_button())
    elif data == 'info':
        await query.edit_message_text("ℹ️ Emerald ModularBot v1.0", reply_markup=back_button())
    elif data == 'support':
        await query.edit_message_text("Напишите сообщение — я передам его владельцу.", reply_markup=back_button())
    elif data == 'admin':
        if query.from_user.id == OWNER_ID:
            await query.edit_message_text("👑 Панель владельца. Полный контроль.", reply_markup=back_button())
        else:
            await query.edit_message_text("🛠 Админ-панель: доступ ограничен.", reply_markup=back_button())
    elif data == 'back':
        await query.edit_message_text("🏠 Главное меню:", reply_markup=main_menu())
    return MENU

async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    user = update.effective_user
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"📨 Сообщение от @{user.username or user.first_name}:\n{msg}"
    )
    await update.message.reply_text("✅ Сообщение отправлено.")
    return MENU

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⛔ Только в группе.")
        return
    if not context.args:
        await update.message.reply_text("❗ Используй: /ban @username")
        return
    try:
        user_to_ban = update.message.entities[1].user
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_ban.id)
        await update.message.reply_text(f"🚫 @{user_to_ban.username or user_to_ban.first_name} забанен.")
    except:
        await update.message.reply_text("❌ Не удалось забанить.")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⛔ Только в группе.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❗ Используй: /mute @username 10m")
        return
    try:
        user_to_mute = update.message.entities[1].user
        duration = parse_duration(context.args[1])
        until_date = update.message.date + duration
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_to_mute.id,
            permissions={}, until_date=until_date
        )
        await update.message.reply_text(f"🤐 @{user_to_mute.username or user_to_mute.first_name} замьючен на {context.args[1]}.")
    except:
        await update.message.reply_text("❌ Не удалось замьютить.")

def parse_duration(s: str):
    match = re.match(r'^(\d+)([smhd])$', s)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if unit == 's': return timedelta(seconds=value)
    if unit == 'm': return timedelta(minutes=value)
    if unit == 'h': return timedelta(hours=value)
    if unit == 'd': return timedelta(days=value)
    return None

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(handle_buttons),
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_forward)
            ]
        },
        fallbacks=[],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("mute", mute_command))

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    import os
    main()
