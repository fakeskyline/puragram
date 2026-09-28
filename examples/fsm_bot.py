from zeed import Bot, RemoveKeyboard, State, StatesGroup

TOKEN = "YOUR_TOKEN_HERE"
bot = Bot(TOKEN, parse_mode="HTML")


class Form(StatesGroup):
    name = State()
    age = State()
    city = State()


@bot.message_handler(commands=["start"])
def start(msg, data):
    data["state"].set_state(Form.name)
    bot.send_message(msg.chat.id, "Hi! What's your name?")


@bot.message_handler(state=Form.name)
def on_name(msg, data):
    ctx = data["state"]
    ctx.update_data(name=msg.text)
    ctx.set_state(Form.age)
    bot.send_message(msg.chat.id, f"Nice to meet you, {msg.text}! How old are you?")


@bot.message_handler(state=Form.age)
def on_age(msg, data):
    ctx = data["state"]
    if not msg.text.isdigit():
        bot.send_message(msg.chat.id, "Please enter a number.")
        return
    ctx.update_data(age=int(msg.text))
    ctx.set_state(Form.city)
    bot.send_message(msg.chat.id, "Which city are you from?")


@bot.message_handler(state=Form.city)
def on_city(msg, data):
    ctx = data["state"]
    ctx.update_data(city=msg.text)
    info = ctx.get_data()
    ctx.clear()
    bot.send_message(
        msg.chat.id,
        f"Done!\nName: {info['name']}\nAge: {info['age']}\nCity: {info['city']}",
        reply_markup=RemoveKeyboard(),
    )


if __name__ == "__main__":
    bot.run_polling()