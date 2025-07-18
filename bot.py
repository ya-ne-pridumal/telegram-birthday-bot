import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Этапы диалога
MONTH, DAY, TIME = range(3)

# Словарь с месяцами
months_ru = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5,
    "июнь": 6, "июль": 7, "август": 8, "сентябрь": 9,
    "октябрь": 10, "ноябрь": 11, "декабрь": 12
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пожалуйста, укажи месяц своего рождения (пример: март)."
    )
    return MONTH

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text in months_ru:
        context.user_data['month'] = months_ru[text]
        await update.message.reply_text("Теперь введи число месяца (пример: 15).")
        return DAY
    else:
        await update.message.reply_text("Пожалуйста, введи корректное название месяца.")
        return MONTH

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        day = int(update.message.text)
        if 1 <= day <= 31:
            context.user_data['day'] = day
            await update.message.reply_text("Теперь введи текущее время (пример: 20:45).")
            return TIME
        else:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Неверный формат. Пример: 15")
        return DAY

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_text = update.message.text
        now = datetime.datetime.now()
        hour, minute = map(int, time_text.split(":"))
        birth_date = datetime.date(now.year, context.user_data['month'], context.user_data['day'])

        if birth_date < now.date():
            birth_date = datetime.date(now.year + 1, context.user_data['month'], context.user_data['day'])

        days_left = (birth_date - now.date()).days
        context.user_data['birth_date'] = birth_date

        await update.message.reply_text(
            f"Установил дату вашего рождения! До вашего дня рождения осталось {days_left} дней."
        )
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text("Неверный формат. Пример: 20:45")
        return TIME

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = context.user_data
    if 'birth_date' in user:
        today = datetime.date.today()
        bd = user['birth_date']

        if today == bd:
            await update.message.reply_text(
                "🎂🥳 Вот и наступил день вашего дня рождения!\n"
                "Желаю успехов в жизни, здоровья, сил и свободного времени!\n"
                "Проведите этот день так, как вам хочется."
            )
        else:
            days_left = (bd - today).days
            await update.message.reply_text(f"До вашего дня рождения осталось {days_left} дней.")
    else:
        await update.message.reply_text("Пожалуйста, начните с команды /start")

def main():
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_month)],
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))

    app.run_polling()

if __name__ == "__main__":
    main()