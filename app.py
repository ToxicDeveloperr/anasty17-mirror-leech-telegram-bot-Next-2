# app.py
import os
from threading import Thread
from flask import Flask, jsonify, request
import asyncio

# === Global Variables ===
# Ye variables bot aur web server ke beech bridge ka kaam karenge
app = Flask(__name__)
telegram_bot_instance = None
bot_event_loop = None

# === Bot Initialization Function ===
def initialize_bot():
    """Bot ko shuru karta hai aur zaroori variables set karta hai."""
    global telegram_bot_instance, bot_event_loop
    
    # Lazy import: Sirf is function ke andar import karein
    from bot import main as start_bot_main, bot_loop as bl, bot as bot_obj, __version__
    
    print(f"Bot version {__version__} starting up in a background thread...")
    bot_event_loop = bl
    
    # Bot ko shuru karein
    bot_event_loop.run_until_complete(start_bot_main())
    
    # Bot ke object ko global variable mein save karein
    telegram_bot_instance = bot_obj
    print(">>> Bot has been initialized and is now ready. <<<")
    
    # Bot ke event loop ko hamesha chalne dein
    bot_event_loop.run_forever()

# === Flask Web Routes ===
@app.route('/')
def home():
    if telegram_bot_instance:
        return f"Hello from Tech J. Bot is running and ready."
    else:
        return "Hello from Tech J. Bot is still initializing, please wait..."

@app.route('/health')
def health():
    return jsonify(status="ok")

@app.route('/api', methods=['GET'])
def api_trigger():
    if not telegram_bot_instance:
        return jsonify({"status": "error", "message": "Bot is not ready yet. Please try again."}), 503

    url_to_leech = request.args.get('url')
    if not url_to_leech:
        return jsonify({"status": "error", "message": "URL parameter is missing."}), 400

    from bot.modules import leech
    from bot.helper.telegram_helper.bot_commands import BotCommands

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
                print(f"Error sending status message: {e}")
            return self

    command_text = f"/{BotCommands.LeechCommand} {url_to_leech}"
    dummy_message_object = DummyMessage(command_text)
    
    # Leech function (coroutine) ko bot ke event loop mein schedule karein
    # Ye thread-safe tarika hai
    asyncio.run_coroutine_threadsafe(
        leech(telegram_bot_instance, dummy_message_object), 
        bot_event_loop
    )

    return jsonify({"status": "success", "message": f"Leech command triggered for: {url_to_leech}"})

# === Main Execution Block ===
# Bot ko ek background thread mein shuru karein, jaise hi app load hota hai
print("Starting bot initialization thread...")
bot_thread = Thread(target=initialize_bot)
bot_thread.daemon = True
bot_thread.start()

# Gunicorn is block ko istemal nahi karega, ye sirf local testing ke liye hai
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
