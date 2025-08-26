import os
from threading import Thread
from flask import Flask, jsonify, request

# =================================================================
# ===== BOT KE ZAROORI MODULES KO IMPORT KAREIN ===================
# =================================================================
# Ye imports aapke bot ke structure ke hisab se honge.
# Agar ye file aapke bot ke root folder mein hai, to ye sahi kaam karega.
# Agar nahi, to aapko 'bot.' prefix hatana ya badalna pad sakta hai.
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.modules import leech  # Leech function ko import karein
from bot import bot, bot_loop, main, LOGGER
# =================================================================

app = Flask(__name__)

# Leech function ko trigger karne ke liye ek function
def trigger_leech(bot_instance, message_instance):
    # Ek naye thread mein leech function ko chalayein taaki web server block na ho
    leech_thread = Thread(target=leech, args=(bot_instance, message_instance))
    leech_thread.start()

@app.route('/')
def home():
    return "Hello from Tech J"

@app.route('/health')
def health():
    return jsonify(status="ok")

# =================================================================
# ===== API ENDPOINT JO LEECH COMMAND KO TRIGGER KAREGA =========
# =================================================================
@app.route('/api', methods=['GET'])
def api_trigger():
    # Request se 'url' parameter ko nikalein
    url_to_leech = request.args.get('url')

    if not url_to_leech:
        return jsonify({"status": "error", "message": "URL parameter is missing. Use ?url=<your_url>"}), 400

    # Leech function ko call karne ke liye ek nakli (dummy) message object banayein
    # Isse leech function ko lagega ki use Telegram se message mila hai
    class DummyUser:
        # Yahan aapki (owner ki) Telegram ID honi chahiye
        # taaki bot is command ko authorized maane
        id = bot.owner_id

    class DummyMessage:
        def __init__(self, text):
            self.text = text
            self.from_user = DummyUser()
            # Leech function status updates bhejta hai, isliye is function ka hona zaroori hai
            self.reply = self
            self.reply_text = self.dummy_reply_text

        async def dummy_reply_text(self, text, *args, **kwargs):
            # API se trigger hone par bot Telegram par message bhejega
            # Yahan hum OWNER_ID ko message bhej rahe hain
            try:
                await bot.send_message(chat_id=self.from_user.id, text=f"API Triggered Status:\n\n{text}")
            except Exception as e:
                LOGGER.error(f"Failed to send API status message: {e}")
            return self # Return self to allow chaining if any

    # Bilkul waisa hi message text banayein jaisa Telegram se aata hai
    command_text = f"/{BotCommands.LeechCommand} {url_to_leech}"
    dummy_message_object = DummyMessage(command_text)

    # Leech function ko trigger karein
    trigger_leech(bot, dummy_message_object)

    # API call karne wale ko success response bhejein
    return jsonify({"status": "success", "message": f"Leech command triggered for: {url_to_leech}"})
# =================================================================

if __name__ == "__main__":
    # Web server ko ek alag thread mein shuru karein
    port = int(os.environ.get("PORT", 8080))
    web_server_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False))
    web_server_thread.daemon = True
    web_server_thread.start()
    
    LOGGER.info("Web server started in a background thread.")

    # Telegram bot ko shuru karein
    # Ye maan kar ki aapka bot 'bot.py' ya '__main__.py' se chalta hai
    if bot_loop.is_running():
        LOGGER.info("Bot is already running.")
    else:
        LOGGER.info("Starting bot loop...")
        bot_loop.run_until_complete(main())
        bot_loop.run_forever()
