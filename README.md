# puragram

A fast, dependency-light Telegram Bot API framework for Python.
Built on urllib3 — no aiohttp, no requests, no httpx.

## Install

```bash
pip install puragram
```

## Quick start

```python
from puragram import Bot

bot = Bot("YOUR_TOKEN", parse_mode="HTML")

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, f"Hi, <b>{msg.from_user.first_name}</b>!")

@bot.message_handler(content_types=["text"])
def echo(msg):
    bot.send_message(msg.chat.id, f"You said: <b>{msg.text}</b>")

if __name__ == "__main__":
    bot.run_polling()
```

## Features

- Fast: direct urllib3 pool, JSON bodies, keep-alive
- Built-in FSM: State, StatesGroup, MemoryStorage, FileStorage, SQLiteStorage
- Middleware: logging, throttling, timing
- Filters: Command, Text, Regexp, ContentTypes, ChatType, ChatId, UserId, CallbackData, Func
- Webhook server on stdlib http.server
- Secure: path traversal guard, size limits, ReDoS filter, webhook secret, token redaction, dedup
- Zero dependencies except urllib3

## FSM example

```python
from puragram import Bot, State, StatesGroup

bot = Bot("YOUR_TOKEN")

class Form(StatesGroup):
    name = State()

@bot.message_handler(commands=["start"])
def start(msg, data):
    data["state"].set_state(Form.name)
    bot.send_message(msg.chat.id, "Your name?")

@bot.message_handler(state=Form.name)
def on_name(msg, data):
    data["state"].update_data(name=msg.text)
    data["state"].clear()
    bot.send_message(msg.chat.id, f"Hi, {msg.text}!")

bot.run_polling()
```

## License

MIT — see LICENSE.