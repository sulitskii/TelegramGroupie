import os
import logging
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')

# Initialize the application
application = Application.builder().token(TELEGRAM_TOKEN).build()

logging.basicConfig(level=logging.INFO)

# Stub processing function
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Received message: {update.message.text}")
    # TODO: Implement processing logic here

# Handler for all group messages
async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_message(update, context)

# Add handler
application.add_handler(MessageHandler(filters.ChatType.GROUPS, group_message_handler))

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