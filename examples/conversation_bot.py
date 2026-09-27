"""Example: multi-step conversation using generators."""
import logging

from puragram import Bot, ConversationCancelled, setup_logging

setup_logging(level=logging.INFO)

TOKEN = "YOUR_TOKEN_HERE"
bot = Bot(TOKEN, parse_mode="HTML")


@bot.conversation(commands=["register"], timeout=300)
def registration(conv):
    name = yield "What's your name?"
    age = yield f"Nice to meet you, <b>{name}</b>. How old are you?"
    if not str(age).isdigit():
        conv.reply("Age must be a number. Try /register again.")
        return
    city = yield "Which city are you from?"
    conv.reply(
        f"<b>Profile saved:</b>\n"
        f"Name: {name}\n"
        f"Age: {age}\n"
        f"City: {city}"
    )


@bot.conversation(commands=["order"], timeout=180)
def order_pizza(conv):
    size = yield "Pizza size? (small / medium / large)"
    if size.lower() not in ("small", "medium", "large"):
        conv.reply("Unknown size. Cancelled.")
        return
    topping = yield "Topping? (cheese / pepperoni / mushroom)"
    conv.reply(f"Order: {size} pizza with {topping}. Confirmed!")


@bot.conversation(commands=["survey"], timeout=600)
def survey(conv):
    rating = yield "How would you rate puragram from 1 to 10?"
    if rating == "0":
        conv.cancel("Thanks anyway.")
        return
    comment = yield "Thanks! Any comments?"
    conv.reply(f"Rating: {rating}/10. Comment: {comment}")


@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "Hi! Try:\n"
        "/register — profile\n"
        "/order — pizza order\n"
        "/survey — leave feedback\n"
        "/cancel — stop current dialog",
    )


@bot.message_handler(content_types=["text"])
def fallback(msg):
    bot.send_message(msg.chat.id, "Use /register, /order, or /survey.")


if __name__ == "__main__":
    bot.run_polling()