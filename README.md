# puragram

**Fast, dependency-light Telegram Bot API framework built on urllib3.**
No aiohttp. No requests. No httpx.

[![PyPI version](https://img.shields.io/pypi/v/puragram.svg)](https://pypi.org/project/puragram/)
[![Python versions](https://img.shields.io/pypi/pyversions/puragram.svg)](https://pypi.org/project/puragram/)
[![License](https://img.shields.io/pypi/l/puragram.svg)](https://github.com/fakeskyline/puragram/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/puragram.svg)](https://pypi.org/project/puragram/)

---

## Why puragram?

Most Telegram Python libraries pull in `aiohttp` or `requests`. `puragram`
talks directly to the Telegram Bot API through `urllib3` with a keep-alive
connection pool. That means:

- **Small** — no heavy dependencies, just `urllib3`
- **Fast** — direct JSON requests, no middleware layers
- **Sync** — simple, predictable, easy to debug

## Features

- Long-polling and webhook (pure stdlib `http.server`)
- **Inline mode** — `@yourbot query` with results
- Built-in FSM: `State`, `StatesGroup`, `MemoryStorage`, `FileStorage`, `SQLiteStorage`
- Middleware: logging, throttling, timing
- Filters: `Command`, `Text`, `Regexp`, `ContentTypes`, `ChatType`, `ChatId`, `UserId`, `CallbackData`, `CallbackDataPrefix`, `Func`
- Filter operators: `&` (and), `|` (or), `~` (not)
- File sending: photo, document, video, audio, voice, sticker
- Extras: poll, location, contact, dice
- Auto-split for long messages (`send_long_message`)
- Security: path traversal guard, size limits, ReDoS protection, token redaction, dedup, safe SQLite
- Zero dependencies except `urllib3`

## Install

```bash
pip install puragram
```

Requires Python 3.9+.

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

## FSM example

```python
from puragram import Bot, RemoveKeyboard, State, StatesGroup

bot = Bot("YOUR_TOKEN", parse_mode="HTML")

class Form(StatesGroup):
    name = State()
    age = State()

@bot.message_handler(commands=["start"])
def start(msg, data):
    data["state"].set_state(Form.name)
    bot.send_message(msg.chat.id, "What's your name?")

@bot.message_handler(state=Form.name)
def on_name(msg, data):
    data["state"].update_data(name=msg.text)
    data["state"].set_state(Form.age)
    bot.send_message(msg.chat.id, f"Nice to meet you, {msg.text}. How old are you?")

@bot.message_handler(state=Form.age)
def on_age(msg, data):
    ctx = data["state"]
    if not msg.text.isdigit():
        bot.send_message(msg.chat.id, "Please enter a number.")
        return
    ctx.update_data(age=int(msg.text))
    info = ctx.get_data()
    ctx.clear()
    bot.send_message(
        msg.chat.id,
        f"Done!\nName: {info['name']}\nAge: {info['age']}",
        reply_markup=RemoveKeyboard(),
    )

bot.run_polling()
```

## Inline mode example

```python
from puragram import Bot, InlineQueryResultArticle

bot = Bot("YOUR_TOKEN")

@bot.inline_query_handler()
def on_inline(q):
    results = [
        InlineQueryResultArticle(
            id="1",
            title="Send hello",
            input_message_content={"message_text": "Hello!"},
        ),
    ]
    bot.answer_inline_query(q.id, results)

bot.run_polling()
```

## Middleware

```python
from puragram import Bot, LoggingMiddleware, ThrottlingMiddleware

bot = Bot("YOUR_TOKEN")
bot.middleware(LoggingMiddleware())
bot.middleware(ThrottlingMiddleware(rate=0.5))

@bot.message_handler(content_types=["text"])
def echo(msg):
    bot.send_message(msg.chat.id, msg.text)

bot.run_polling(workers=4)
```

## Webhook

```python
from puragram import Bot, WebhookServer

bot = Bot("YOUR_TOKEN")

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "Hello via webhook!")

if __name__ == "__main__":
    server = WebhookServer(
        bot,
        host="0.0.0.0",
        port=8080,
        path="/webhook",
        secret_token="change-me-to-random-32-chars",
    )
    server.install("https://your-domain.com/webhook")
    server.start(blocking=True)
```

## Security

- **Path traversal** — `safe_path()` rejects `/etc`, `/proc`, `/sys`, `/root`, `/dev`
- **Upload size** — 50 MB limit enforced
- **Callback data** — validated to ≤64 UTF-8 bytes
- **ReDoS** — `compile_safe_regex()` rejects nested quantifiers
- **Webhook forgery** — `hmac.compare_digest` on secret token
- **Token leakage** — bot tokens redacted from logs
- **Idempotency** — duplicate `update_id` dropped via LRU
- **SQL injection** — parameterized queries only

## Documentation

See [ABOUT.md](https://github.com/fakeskyline/puragram/blob/main/ABOUT.md) for a full beginner's guide: Python essentials, HTTP, JSON, Telegram Bot API, FSM, middleware, webhooks, security, testing, and deployment.

## License

MIT — see [LICENSE](https://github.com/fakeskyline/puragram/blob/main/LICENSE).