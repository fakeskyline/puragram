from puragram import Bot, InlineKeyboardMarkup, InlineKeyboardB>

TOKEN = "YOUR_TOKEN_HERE"

bot = Bot(TOKEN, parse_mode="HTML")


@bot.message_handler(commands=["start"])
def on_start(msg):
    kb = InlineKeyboardMarkup().row(
        InlineKeyboardButton("Say hi", callback_data="hi"),
        InlineKeyboardButton("Google", url="https://google.com">
    )
    bot.send_message(
        msg.chat.id,
        f"Hi, <b>{msg.from_user.first_name}</b>!\n"
        f"Press a button or send anything.",
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda q: q.data == "hi")
def on_hi(q):
    bot.answer_callback_query(q.id, text="Hello!")
    bot.send_message(q.message.chat.id, "You pressed the button>


@bot.message_handler(content_types=["text"])
def echo(msg):
    bot.send_message(msg.chat.id, f"You said: <b>{msg.text}</b>>


if __name__ == "__main__":
