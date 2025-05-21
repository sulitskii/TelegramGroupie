import os
import logging
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

app = Flask(__name__)

# Telegram configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')

# Initialize Telegram application
application = Application.builder().token(TELEGRAM_TOKEN).build()

logging.basicConfig(level=logging.INFO)

# Telegram message processing
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Received message: {update.message.text}")
    # TODO: Implement message processing logic here

# Telegram handler for all group messages
async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_message(update, context)

# Add Telegram handler
application.add_handler(MessageHandler(filters.ChatType.GROUPS, group_message_handler))

# Telegram webhook endpoint
@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "ok"
    else:
        abort(403)

@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080))) 