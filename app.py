import os
from threading import Thread
from flask import Flask, jsonify, request

# Flask app banayein
app = Flask(__name__)

# Ye global variable bot ke instance ko hold karega
# jab wo puri tarah se shuru ho jayega
telegram_bot_instance = None

@app.route('/')
def home():
    # Health check endpoint
    return "Hello from Tech J. Bot is running."

@app.route('/health')
def health():
    return jsonify(status="ok")

@app.route('/api', methods=['GET'])
def api_trigger():
    # Jab tak bot puri tarah shuru na ho, tab tak error bhejein
    if not telegram_bot_instance:
        return jsonify({"status": "error", "message": "Bot is not initialized yet. Please try again in a few moments."}), 503

    url_to_leech = request.args.get('url')
    if not url_to_leech:
        return jsonify({"status": "error", "message": "URL parameter is missing. Use ?url=<your_url>"}), 400

    # Jab zaroorat ho, tabhi modules import karein
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
                # Status update owner ko PM mein bhejein
                await telegram_bot_instance.send_message(chat_id=self.from_user.id, text=f"API Triggered Status:\n\n{text}")
            except Exception as e:
                print(f"Failed to send API status message: {e}")
            return self

    command_text = f"/{BotCommands.LeechCommand} {url_to_leech}"
    dummy_message_object = DummyMessage(command_text)

    # Leech function ko naye thread mein chalayein
    Thread(target=leech, args=(telegram_bot_instance, dummy_message_object)).start()

    return jsonify({"status": "success", "message": f"Leech command triggered for: {url_to_leech}"})

def run_bot():
    """Ye function bot ke modules ko import karke bot ko chalata hai."""
    global telegram_bot_instance
    from bot import main as start_bot_main, bot_loop, bot as bot_obj
    
    # Bot ko shuru karein
    bot_loop.run_until_complete(start_bot_main())
    
    # Bot ke instance ko global variable mein save karein
    telegram_bot_instance = bot_obj
    
    # Bot ko hamesha chalate rahein
    bot_loop.run_forever()

if __name__ == "__main__":
    # Bot ko background thread mein shuru karein
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Flask web server ko main thread mein chalayein
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
