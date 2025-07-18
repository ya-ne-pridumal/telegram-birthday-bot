import os
import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

MONTH, DAY, TIME = range(3)
months_ru = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5,
    "июнь": 6, "июль": 7, "август": 8, "сентябрь": 9,
    "октябрь": 10, "ноябрь": 11, "декабрь": 12
}

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Например: "8e5f96ac832f16518ff1a5a99870827a"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Укажи месяц рождения (пример: март).")
    return MONTH

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text in months_ru:
        context.user_data['month'] = months_ru[text]
        await update.message.reply_text("Теперь введи число (пример: 15).")
        return DAY
    await update.message.reply_text("Неверный месяц.")
    return MONTH

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        day = int(update.message.text)
        if 1 <= day <= 31:
            context.user_data['day'] = day
            await update.message.reply_text("Теперь введи время (пример: 20:45).")
            return TIME
    except:
        pass
    await update.message.reply_text("Неверный формат дня.")
    return DAY

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hour, minute = map(int, update.message.text.split(":"))
        now = datetime.datetime.now()
        birth_date = datetime.date(now.year, context.user_data['month'], context.user_data['day'])
        if birth_date < now.date():
            birth_date = datetime.date(now.year + 1, context.user_data['month'], context.user_data['day'])
        context.user_data['birth_date'] = birth_date
        days_left = (birth_date - now.date()).days
        await update.message.reply_text(f"Дата установлена! Осталось {days_left} дней.")
        return ConversationHandler.END
    except:
        await update.message.reply_text("Неверный формат времени.")
        return TIME

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'birth_date' in context.user_data:
        today = datetime.date.today()
        bd = context.user_data['birth_date']
        if today == bd:
            await update.message.reply_text("🎉 С днём рождения!")
        else:
            days_left = (bd - today).days
            await update.message.reply_text(f"Осталось {days_left} дней.")
    else:
        await update.message.reply_text("Сначала /start")

flask_app = Flask(__name__)

async def setup_webhook(app):
    webhook_url = os.getenv("WEBHOOK_URL")  # Например: "https://your-app.onrender.com"
    await app.bot.set_webhook(f"{webhook_url}/{WEBHOOK_SECRET}")

telegram_app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).post_init(setup_webhook).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_month)],
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
        TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
    },
    fallbacks=[]
)

telegram_app.add_handler(conv_handler)
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))

@flask_app.post(f"/{WEBHOOK_SECRET}")
async def webhook():
    data = request.get_json(force=True)
    await telegram_app.update_queue.put(Update.de_json(data, telegram_app.bot))
    return {"ok": True}

if __name__ == "__main__":
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:10000"]  # Render требует порт, например 10000
    import asyncio
    asyncio.run(serve(flask_app, config))