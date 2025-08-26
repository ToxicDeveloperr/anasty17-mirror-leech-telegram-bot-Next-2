# app.py

import os
from threading import Thread
from flask import Flask, jsonify, request
from bot import main as start_bot, bot_loop, __version__

# Step 1: Ek Flask app banayein
app = Flask(__name__)

# Global variable bot ko store karne ke liye
telegram_bot_instance = None

# Step 2: Health check endpoint, jise Koyeb use karega
@app.route('/')
def home():
    # Version number dikhayein taki pata chale ki app chal raha hai
    return f"Bot is running! Version: {__version__}"

@app.route('/health')
def health():
    return jsonify(status="ok")

# Step 3: API endpoint jo leech command ko trigger karega
@app.route('/api', methods=['GET'])
def api_trigger():
    global telegram_bot_instance
    if not telegram_bot_instance:
        return jsonify({"status": "error", "message": "Bot is not initialized yet. Please try again in a moment."}), 503

    url_to_leech = request.args.get('url')
    if not url_to_leech:
        return jsonify({"status": "error", "message": "URL parameter is missing. Use ?url=<your_url>"}), 400

    # Lazy import: Jab zaroorat ho tabhi import karein
    from bot.modules import leech
    from bot.helper.telegram_helper.bot_commands import BotCommands

    # Nakli message object banayein
    class DummyUser:
        id = telegram_bot_instance.owner_id

    class DummyMessage:
        def __init__(self, text):
            self.text = text
            self.from_user = DummyUser()
            self.reply = self
            self.reply_text = self.dummy_reply_text

        async def dummy_reply_text(self, text, *args, **kwargs):
            try:
                await telegram_bot_instance.send_message(chat_id=self.from_user.id, text=f"API Triggered Status:\n\n{text}")
            except Exception as e:
                print(f"Failed to send API status message: {e}")
            return self

    command_text = f"/{BotCommands.LeechCommand} {url_to_leech}"
    dummy_message_object = DummyMessage(command_text)

    # Leech function ko ek naye thread mein chalayein
    Thread(target=leech, args=(telegram_bot_instance, dummy_message_object)).start()

    return jsonify({"status": "success", "message": f"Leech command triggered for: {url_to_leech}"})

# Step 4: Bot ko shuru karne ka function
def run_bot():
    global telegram_bot_instance
    # Bot ko shuru karein
    bot_loop.run_until_complete(start_bot())
    # Bot instance ko global variable mein save karein
    from bot import bot as bot_instance
    telegram_bot_instance = bot_instance
    # Bot ko hamesha chalne dein
    bot_loop.run_forever()

# Step 5: Main execution block
if __name__ == "__main__":
    # Bot ko ek background thread mein shuru karein
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Flask web server ko main thread mein chalayein
    # Gunicorn is block ko istemal nahi karega, lekin local testing ke liye ye zaroori hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

