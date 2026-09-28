import logging

from zeed import (
    Bot, LoggingMiddleware, ThrottlingMiddleware, TimingMiddleware,
    setup_logging,
)

TOKEN = "YOUR_TOKEN_HERE"

setup_logging(level=logging.INFO)
bot = Bot(TOKEN)

bot.middleware(LoggingMiddleware())
bot.middleware(ThrottlingMiddleware(rate=0.5))
bot.middleware(TimingMiddleware(threshold=0.3))


@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "Hi! No spam - I'm throttled.")


@bot.message_handler(commands=["slow"])
def slow(msg):
    import time
    time.sleep(0.5)
    bot.send_message(msg.chat.id, "That was a slow handler.")


@bot.message_handler(content_types=["text"])
def echo(msg):
    bot.send_message(msg.chat.id, f"You: {msg.text}")


if __name__ == "__main__":
    bot.run_polling(workers=2)