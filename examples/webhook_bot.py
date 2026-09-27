from puragram import Bot, WebhookServer

TOKEN = "YOUR_TOKEN_HERE"
PUBLIC_URL = "https://your-public-url/webhook"
SECRET = "change-me-to-random-32-chars-please"

bot = Bot(TOKEN, parse_mode="HTML")


@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "Hello via webhook!")


@bot.message_handler(content_types=["text"])
def echo(msg):
    bot.send_message(msg.chat.id, f"You: {msg.text}")


if __name__ == "__main__":
    server = WebhookServer(bot, host="0.0.0.0", port=8080,
                           path="/webhook", secret_token=SECRET)
    print(f"Registering URL: {PUBLIC_URL}")
    server.install(PUBLIC_URL)
    print("Server listening on 0.0.0.0:8080/webhook")
    server.start(blocking=True)