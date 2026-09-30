# About zeed — Learn Python & Bots From Zero

This document is a full beginner's guide. It teaches you Python, HTTP,
JSON, and Telegram bots from scratch, and explains every design decision
inside `zeed`. Read it end-to-end once — you will understand not just
this library, but how any Telegram bot framework works under the hood.

Current version: **1.2.2**

---

## Table of Contents

1. [What is a Telegram bot](#1-what-is-a-telegram-bot)
2. [Python essentials](#2-python-essentials)
3. [HTTP in 10 minutes](#3-http-in-10-minutes)
4. [JSON and data](#4-json-and-data)
5. [How Telegram Bot API works](#5-how-telegram-bot-api-works)
6. [Reading the zeed source](#6-reading-the-zeed-source)
7. [Writing your first bot](#7-writing-your-first-bot)
8. [Handlers, filters, and dispatch](#8-handlers-filters-and-dispatch)
9. [Finite State Machines (FSM)](#9-finite-state-machines-fsm)
10. [Middleware](#10-middleware)
11. [Webhooks vs long-polling](#11-webhooks-vs-long-polling)
12. [Security — why it matters](#12-security--why-it-matters)
13. [Testing your code](#13-testing-your-code)
14. [Deploying a bot](#14-deploying-a-bot)
15. [Inline mode and extra methods](#15-inline-mode-and-extra-methods)
16. [Conversation handler](#16-conversation-handler)
17. [Further reading](#17-further-reading)

---

## 1. What is a Telegram bot

A **Telegram bot** is an automated account. You talk to it like a person,
but a computer answers. Bots can:

- Send and edit messages
- Show buttons and keyboards
- Receive photos, files, locations
- Answer inline queries (when users type `@yourbot query`)
- Accept payments

Every bot is controlled by a program running on a server (or on your
phone, as you can do with Termux). That program talks to **Telegram Bot
API** — a set of HTTPS endpoints Telegram exposes at
`https://api.telegram.org`.

You get a **token** from @BotFather. It looks like:

```
1234567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Anyone with this token can control the bot. **Never commit it to GitHub.**

---

## 2. Python essentials

You need about 20% of Python to write serious bots. Here they are.

### 2.1 Variables and types

```python
name = "Alice"       # str
age = 25             # int
pi = 3.14            # float
is_active = True     # bool
nothing = None       # NoneType
```

### 2.2 Lists, dicts, tuples

```python
fruits = ["apple", "banana", "cherry"]     # list — ordered, mutable
person = {"name": "Bob", "age": 30}        # dict — key to value
point = (10, 20)                           # tuple — ordered, immutable
```

### 2.3 Conditions

```python
if age >= 18:
    print("adult")
elif age >= 13:
    print("teen")
else:
    print("child")
```

### 2.4 Loops

```python
for fruit in fruits:
    print(fruit)

for i in range(5):     # 0, 1, 2, 3, 4
    print(i)

while True:
    answer = input("? ")
    if answer == "quit":
        break
```

### 2.5 Functions

```python
def greet(name, punctuation="!"):
    return f"Hello, {name}{punctuation}"

greet("Alice")            # "Hello, Alice!"
greet("Bob", "?")         # "Hello, Bob?"
```

### 2.6 Classes

```python
class Dog:
    def __init__(self, name):
        self.name = name

    def bark(self):
        return f"{self.name} says woof"

rex = Dog("Rex")
print(rex.bark())
```

`self` is the instance. `__init__` is the constructor.

### 2.7 Modules and imports

A **module** is a `.py` file. A **package** is a folder with `__init__.py`.

```python
# inside myfile.py
import math
from math import sqrt
from .sibling import helper    # relative import
```

### 2.8 Exceptions

```python
try:
    x = 1 / 0
except ZeroDivisionError as e:
    print("caught:", e)
finally:
    print("always runs")
```

### 2.9 Decorators

A decorator wraps a function. It is just a function that takes a function.

```python
def logged(func):
    def wrapper(*args, **kwargs):
        print("calling", func.__name__)
        return func(*args, **kwargs)
    return wrapper

@logged
def hello():
    print("hi")

hello()   # prints "calling hello", then "hi"
```

`@bot.message_handler(...)` in `zeed` is a decorator. It registers
your function so the bot calls it when a matching message arrives.

### 2.10 Type hints

```python
def add(a: int, b: int) -> int:
    return a + b
```

Python does not enforce them at runtime, but tools (mypy, pyright, IDE)
use them to catch bugs before you run code. Use them everywhere.

---

## 3. HTTP in 10 minutes

Your bot talks to Telegram over **HTTPS**.

### 3.1 Request

```
POST /bot123456:ABC/getUpdates HTTP/1.1
Host: api.telegram.org
Content-Type: application/json

{"offset": 100, "timeout": 30}
```

Parts:

- **Method** — `GET`, `POST`, `PUT`, `DELETE`
- **Path** — `/bot<token>/<methodName>`
- **Headers** — metadata (`Content-Type`, `Authorization`, etc.)
- **Body** — data (JSON, form, or binary)

### 3.2 Response

```
HTTP/1.1 200 OK
Content-Type: application/json

{"ok": true, "result": [...]}
```

- **Status code** — 200 OK, 400 Bad Request, 404 Not Found, 500 Server Error
- **Body** — usually JSON

### 3.3 Why HTTPS matters

Plain HTTP is readable by anyone on the network. HTTPS encrypts traffic
using TLS. Telegram **only** accepts HTTPS. Never send a bot token over
HTTP.

### 3.4 Keep-alive

Opening a new TCP + TLS connection per request is slow (~100 ms).
`urllib3` keeps connections alive in a **pool**. `zeed` uses
`PoolManager` with `pool_size` connections. This is why it can be
faster than naive code that opens a new connection every time.

Starting from `zeed 1.1.1`, `PoolManager` is configured with
`block=True` (wait for a free connection), `TCP_NODELAY` (disable
Nagle's algorithm for small JSON payloads), and `SO_KEEPALIVE`
(keep connections open). Together these reduce latency and jitter.

---

## 4. JSON and data

JSON is the universal data format.

```json
{
  "update_id": 123456,
  "message": {
    "message_id": 42,
    "date": 1700000000,
    "chat": { "id": 111, "type": "private" },
    "from": { "id": 111, "is_bot": false, "first_name": "Alice" },
    "text": "/start"
  }
}
```

In Python:

```python
import json

data = json.loads('{"a": 1}')    # str to dict
text = json.dumps({"a": 1})      # dict to str
```

`zeed` parses every Telegram response into Python **dataclasses**
(`Message`, `Chat`, `User`, `CallbackQuery`) so you can write
`msg.text` instead of `msg["text"]`.

---

## 5. How Telegram Bot API works

### 5.1 Getting updates — two modes

**Long-polling**: your program repeatedly asks Telegram "any new updates?".
The connection stays open until either an update arrives or `timeout`
seconds pass.

```python
updates = api.call("getUpdates", offset=next_offset, timeout=30)
```

**Webhook**: you give Telegram a URL. It POSTs updates to you as they
arrive.

Long-polling is easier. Webhooks scale better.

### 5.2 Sending messages

```
POST https://api.telegram.org/bot<TOKEN>/sendMessage
{"chat_id": 111, "text": "Hello"}
```

Response:

```json
{
  "ok": true,
  "result": {
    "message_id": 43,
    "date": 1700000001,
    "chat": { "id": 111, "type": "private" },
    "text": "Hello"
  }
}
```

### 5.3 Offset

Every update has `update_id`. When you call `getUpdates`, you pass
`offset = last_update_id + 1`. Telegram then acknowledges everything
before that offset and never returns it again.

### 5.4 Method names are camelCase

Telegram API uses `getMe`, `sendMessage`, `getUpdates`. Python convention
is `get_me`, `send_message`. `zeed` exposes the Python name and
converts automatically via `_camel()` in `api.py`. This is a common
source of confusion — if you get `404 Not Found`, check that the method
name is being converted correctly.

### 5.5 Rate limits

Telegram limits:

- ~30 messages per second per chat
- ~20 messages per minute to a group
- 429 Too Many Requests comes with `retry_after` seconds

`zeed` does **not** retry on 429 by default. You should catch the
error and sleep before retrying. An unbounded retry loop would make
things worse, not better.

---

## 6. Reading the zeed source

Open the `zeed/` folder and read files in this order:

1. **`exceptions.py`** — what can go wrong
2. **`security.py`** — all safety helpers
3. **`logger.py`** — logging setup with token redaction
4. **`utils.py`** — small string helpers
5. **`types.py`** — dataclasses for Telegram objects
6. **`keyboards.py`** — inline and reply keyboards
7. **`filters.py`** — decorator predicates
8. **`api.py`** — HTTP layer over urllib3
9. **`middleware.py`** — request interceptors
10. **`fsm/`** — finite state machine
11. **`webhook.py`** — HTTP server on stdlib
12. **`bot.py`** — the main `Bot` class
13. **`__init__.py`** — public exports

Each file is under 300 lines. If you understand them all, you can write
your own framework.

---

## 7. Writing your first bot

```python
from zeed import Bot

TOKEN = "1234567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
bot = Bot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(msg.chat.id, f"Hi, <b>{msg.from_user.first_name}</b>!")

@bot.message_handler(content_types=["text"])
def echo(msg):
    bot.send_message(msg.chat.id, f"You said: <b>{msg.text}</b>")

if __name__ == "__main__":
    bot.run_polling()
```

Save as `mybot.py`. Run `python mybot.py`. Message your bot on Telegram.

### What happens step by step

1. `Bot(TOKEN)` creates a `TelegramAPI` instance with a connection pool.
2. `@bot.message_handler(...)` registers your function in `bot._handlers`.
3. `bot.run_polling()` calls `getUpdates` in a loop, parses each update
   into an `Update` object, and dispatches it to matching handlers.

---

## 8. Handlers, filters, and dispatch

A **handler** is `(kind, function, filter, state)`.

`kind` is one of: `message`, `edited_message`, `channel_post`,
`edited_channel_post`, `callback_query`, `inline_query`.

A **filter** decides whether a handler should run for a given update.
`zeed` supports both keyword filters:

```python
@bot.message_handler(commands=["start"], chat_types=["private"])
```

and filter objects:

```python
from zeed import Command, ChatType

@bot.message_handler(Command("start") & ChatType("private"))
```

Operators: `&` = AND, `|` = OR, `~` = NOT.

### Filter classes

| Class | Matches |
|---|---|
| `Command("start", "help")` | `/start` or `/help` |
| `Text("yes", "no")` | exact text (case-insensitive) |
| `Regexp(r"^\d+$")` | regex against text |
| `ContentTypes("photo", "video")` | message content type |
| `ChatType("private", "group")` | chat type |
| `ChatId(12345)` | specific chat |
| `UserId(12345)` | specific user |
| `CallbackData("yes", "no")` | exact button press data |
| `CallbackDataPrefix("menu:")` | button data with prefix |
| `InlineQueryText("hello")` | inline query text |
| `Func(lambda m: m.text == "hi")` | any Python predicate |

### Dispatch loop

Inside `Bot._dispatch`, we iterate over `(kind, obj)` pairs. For each
update field that is set (e.g. `update.message`), we loop through all
handlers of that kind. If the handler has a filter, we call it. If the
handler has a state, we check the FSM. If both pass, we call the function.

```python
for kind, obj in pairs:
    if obj is None:
        continue
    for h in self._handlers:
        if h.kind != kind:
            continue
        if h.filter and not h.filter(obj):
            continue
        if h.state and fsm.get_state() != h.state:
            continue
        h.invoke(obj, data)
```

This is the heart of every bot framework.


---

## 9. Finite State Machines (FSM)

A **state machine** is a model with discrete states and transitions. Real
example — user registration:

```
        /start
          |
          v
       [ask name]
          | user replies with name
          v
       [ask age]
          | user replies with number
          v
       [ask city]
          | user replies with city
          v
        [done]
```

Without FSM you would store flags manually:

```python
user_data = {}
user_data[user_id] = {"step": "ask_name"}
```

`zeed` FSM does this properly:

```python
from zeed import State, StatesGroup, MemoryStorage

class Form(StatesGroup):
    name = State()
    age = State()
    city = State()

bot = Bot(TOKEN, storage=MemoryStorage())

@bot.message_handler(commands=["start"])
def start(msg, data):
    data["state"].set_state(Form.name)
    bot.send_message(msg.chat.id, "Your name?")

@bot.message_handler(state=Form.name)
def on_name(msg, data):
    data["state"].update_data(name=msg.text)
    data["state"].set_state(Form.age)
    bot.send_message(msg.chat.id, "Your age?")
```

Note the second parameter `data`. `zeed` inspects your function
signature — if it has 2 or more parameters, the second one is a context
dict with `bot`, `state`, and `update`.

### Storage backends

- `MemoryStorage` — dict in RAM. Fast. Lost on restart.
- `FileStorage("fsm.json")` — JSON file. Survives restart.
- `SQLiteStorage("fsm.db")` — database. Survives restart, handles
  concurrency.

All three implement the same interface, so you can swap them freely.

### State keys

The FSM key is derived from `(chat_id, user_id)`. So if 5 users talk to
your bot at once, each has its own state. Two users in the same group
chat also have separate states.

---

## 10. Middleware

A **middleware** sits between dispatch and your handler:

```
update -> middleware1 -> middleware2 -> handler
```

Use cases:

- Log every call
- Limit rate per user
- Measure timing
- Inject shared data
- Catch exceptions

Example:

```python
from zeed import ThrottlingMiddleware

bot.middleware(ThrottlingMiddleware(rate=1.0))   # max 1 msg/sec/user
```

Custom middleware:

```python
from zeed import BaseMiddleware

class BanCheck(BaseMiddleware):
    def __init__(self, banned):
        self.banned = banned

    def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user and user.id in self.banned:
            return None
        return handler(event, data)

bot.middleware(BanCheck({111, 222}))
```

Middleware order is **outermost first**:

```python
bot.middleware(A)
bot.middleware(B)
# runs: A -> B -> your handler
```

---

## 11. Webhooks vs long-polling

### Long-polling

```
loop:
    updates = getUpdates(timeout=30)
    process(updates)
```

**Pros**: no public IP needed, no TLS certificate, easy to run behind NAT.

**Cons**: one HTTP request per bot per 30 s on idle, slightly higher latency.

### Webhooks

```
POST https://yourdomain.com/webhook   <- Telegram pushes updates here
```

**Pros**: lower latency, more efficient at scale.

**Cons**: needs public HTTPS URL, certificate, server infrastructure.

`zeed` provides `WebhookServer` on top of `http.server`:

```python
from zeed import WebhookServer

bot = Bot(TOKEN)
server = WebhookServer(
    bot,
    host="0.0.0.0",
    port=8080,
    path="/webhook",
    secret_token="random-32-chars-please",
)
server.install("https://yourdomain.com/webhook")
server.start(blocking=True)
```

**Always set `secret_token`.** Telegram sends it in a header. If the
header is missing or wrong, `zeed` returns `403 Forbidden` before
touching your handlers. This blocks fake webhook POSTs from attackers.

For local testing, use `cloudflared` or `ngrok` to expose your laptop:

```bash
cloudflared tunnel --url http://localhost:8080
```

---

## 12. Security — why it matters

A Telegram bot is a **public endpoint**. Anyone can:

- Send it messages
- Press its buttons
- Post to its webhook URL

`zeed` ships with defenses for common attacks.

### 12.1 Path traversal

If you accept a filename from a user and open it:

```python
open(msg.text)          # DANGEROUS — user sends "../../etc/passwd"
```

`safe_path()` resolves the real path and rejects anything inside
`/etc`, `/proc`, `/sys`, `/root`, `/dev`, or outside `base_dir`:

```python
from zeed import safe_path

path = safe_path(msg.text, base_dir="/sdcard/uploads")
with open(path, "rb") as f:
    ...
```

### 12.2 Upload size limit

Telegram caps at 50 MB. `check_size(path)` raises before you waste
bandwidth.

### 12.3 Callback data length

Telegram limit: 64 bytes UTF-8. `validate_callback_data` raises early
on `\x00` bytes or oversized payloads.

### 12.4 ReDoS

Regular expressions can run forever. `(a+)+$` against `aaaa...ab` is
**exponential**. `compile_safe_regex` rejects patterns containing
nested quantifiers or quantified alternations.

### 12.5 Webhook forgery

Anyone who knows your URL can POST fake updates. `constant_time_eq`
compares the `X-Telegram-Bot-Api-Secret-Token` header using
`hmac.compare_digest`, which prevents timing attacks.

### 12.6 Token leakage

`log.exception()` on an error can print the URL, which contains the token.
`logger.py` replaces any `\d+:[A-Za-z0-9_-]+` with `***REDACTED***`
before writing.

### 12.7 Idempotency

Telegram sometimes delivers the same update twice (rare, but happens on
network retries). `_DedupCache` keeps the last 1024 `update_id` values
in an LRU. Duplicates are skipped.

### 12.8 SQL injection

`SQLiteStorage` uses only parameterized queries:

```python
conn.execute("... WHERE key = ?", (key,))
```

Never build SQL with f-strings.

---

## 13. Testing your code

Install pytest:

```bash
pip install pytest
```

Write a test:

```python
def test_command_filter():
    from zeed import Command
    from zeed.types import Message

    msg = Message.from_dict({
        "message_id": 1, "date": 0,
        "chat": {"id": 1, "type": "private"},
        "text": "/start",
    })
    assert Command("start")(msg)
    assert not Command("help")(msg)
```

Run:

```bash
python -m pytest -v
```

Rules of thumb:

- Test one thing per function
- Name tests `test_<what>_<condition>`
- Use `pytest.raises(ValueError)` for expected failures
- Use `tmp_path` fixture for file tests
- Aim for 80%+ coverage of critical code

`zeed` itself has 84 tests covering filters, FSM, security, and
utilities.

---

## 14. Deploying a bot

Running on your phone is fine for learning. For a real bot:

### Option A — VPS (5 USD/month)

Rent a VPS (Hetzner, DigitalOcean, Scaleway, Ukrainian providers).
Install Python, clone your repo, run as a systemd service:

```ini
[Unit]
Description=My Telegram Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/bot/mybot.py
Restart=always
User=botuser

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mybot
sudo systemctl start mybot
```

### Option B — Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "mybot.py"]
```

```bash
docker build -t mybot .
docker run -d --restart=always mybot
```

### Option C — Free tiers

Railway, Render, Fly.io — free for small bots.

GitHub Actions — only for scheduled tasks, not 24/7 polling.

### Always

- Store token in env var, never in code
- Set up log rotation
- Monitor with `systemctl status`, `journalctl -u mybot -f`

---

## 15. Inline mode and extra methods

Since version 1.1.0, `zeed` supports **inline mode** and additional
Bot API methods.

### 15.1 Inline mode

An **inline query** happens when a user types `@yourbot query` in any
chat. Your bot returns a list of results the user can send.

```python
from zeed import Bot, InlineQueryResultArticle

bot = Bot("YOUR_TOKEN")

@bot.inline_query_handler()
def on_inline(q):
    results = [
        InlineQueryResultArticle(
            id="hello",
            title="Send hello",
            description="A friendly greeting",
            input_message_content={"message_text": "Hello!"},
        ),
    ]
    bot.answer_inline_query(q.id, results, cache_time=5)

bot.run_polling()
```

Enable inline mode via @BotFather: `/mybots` -> your bot ->
Bot Settings -> Inline Mode -> Turn on.

### 15.2 New Bot methods (1.1.0+)

- `send_poll(chat_id, question, options)`
- `send_location(chat_id, latitude, longitude)`
- `send_contact(chat_id, phone_number, first_name)`
- `send_dice(chat_id, emoji="🎲")`
- `send_sticker(chat_id, sticker)`
- `send_long_message(chat_id, text)` — splits long text automatically

### 15.3 New filters (1.1.0+)

- `CallbackDataPrefix("menu:", "nav:")` — match callback data by prefix
- `InlineQueryText("hello")` — match inline query text

### 15.4 Stability (1.1.1+)

- `TCP_NODELAY` — lower latency for small payloads
- `SO_KEEPALIVE` — connections stay open
- `PoolManager(block=True)` — reliable connection reuse
- `retries=0` by default — no hidden delays; opt-in with `Bot(..., retries=2)`
- `connect_timeout` configurable separately from read timeout
- `pool_size` default raised from 10 to 16

### 15.5 Deprecation cleanups (1.1.2+)

- `pyproject.toml` uses `license = "MIT"` (SPDX format)
- `license-files = ["LICENSE"]`
- Removed the deprecated license classifier

---

## 16. Conversation handler

`zeed` ships with a **conversation handler** — a way to write
multi-step dialogs as a single function, using Python generators.

### 16.1 Why not just FSM?

FSM is powerful but verbose. A three-step dialog needs three states,
three handlers, and shared data in a dict. The conversation handler
keeps everything in one place:

```python
# FSM version — three states, three handlers
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()

@bot.message_handler(commands=["register"])
def start(msg, data):
    data["state"].set_state(Form.name)
    bot.send_message(msg.chat.id, "Name?")

@bot.message_handler(state=Form.name)
def on_name(msg, data):
    data["state"].update_data(name=msg.text)
    data["state"].set_state(Form.age)
    bot.send_message(msg.chat.id, "Age?")

@bot.message_handler(state=Form.age)
def on_age(msg, data):
    data["state"].update_data(age=msg.text)
    data["state"].set_state(Form.city)
    bot.send_message(msg.chat.id, "City?")

@bot.message_handler(state=Form.city)
def on_city(msg, data):
    info = data["state"].get_data()
    data["state"].clear()
    bot.send_message(msg.chat.id, f"{info['name']}, {info['age']}, {info['city']}")
```

```python
# Conversation version — one function
@bot.conversation(commands=["register"], timeout=300)
def register(conv):
    name = yield "Name?"
    age = yield "Age?"
    city = yield "City?"
    conv.reply(f"{name}, {age}, {city}")
```

The second one is easier to read, easier to change, and behaves the
same for the user.

### 16.2 How it works

1. The user sends `/register`. `zeed` runs your function until
   the first `yield` and sends the yielded string.
2. The user replies. The reply is sent **back into the generator**,
   becoming the value of the `yield` expression.
3. This continues until the function returns (dialog finished) or
   raises `ConversationCancelled` (dialog aborted).

Internally the handler uses `gen.send(text)` — same mechanism as any
Python generator.

### 16.3 Cancelling a conversation

Two ways:

**1. The user sends `/cancel`** — `zeed` handles this automatically.
No code needed.

**2. Your code raises the cancel**:

```python
@bot.conversation(commands=["order"])
def order(conv):
    size = yield "Size? (small/large)"
    if size == "huge":
        conv.cancel("Sorry, no huge pizzas.")
        return
    conv.reply(f"{size} pizza ordered.")
```

`conv.cancel(msg)` raises `ConversationCancelled(msg)` internally,
sends the message, and stops the dialog.

### 16.4 Timeout

If the user goes silent, the conversation is auto-cancelled. Default
timeout is 300 seconds. Set per-conversation:

```python
@bot.conversation(commands=["survey"], timeout=60)
def survey(conv):
    rating = yield "Rate 1-10?"
    conv.reply(f"Thanks: {rating}")
```

Set `timeout=None` to disable the timeout entirely.

### 16.5 Branching

Conversations can branch like any Python code:

```python
@bot.conversation(commands=["order"])
def order(conv):
    kind = yield "Pizza or burger?"
    if kind == "pizza":
        cheese = yield "Extra cheese? (yes/no)"
        conv.reply(f"Pizza, extra cheese: {cheese}")
    elif kind == "burger":
        sauce = yield "Which sauce?"
        conv.reply(f"Burger with {sauce}")
    else:
        conv.cancel("Unknown option.")
```

For deeply branching flows with many states, FSM may be clearer.
For **linear** dialogs (register, order, survey), conversations win.

### 16.6 Isolated per user

Each `(chat_id, user_id)` has its own conversation instance. In a
group chat, two users can run the same conversation independently.

### 16.7 `ConversationContext`

Your function receives `conv` as the first argument. It has:

- `conv.chat_id` — current chat id
- `conv.user_id` — current user id
- `conv.bot` — the `Bot` instance
- `conv.data` — a plain dict for your own storage
- `conv.reply(text)` — send a message immediately (do not yield)
- `conv.cancel(message=None)` — cancel the conversation

Use `conv.reply()` when you want to send extra messages without
waiting for input:

```python
@bot.conversation(commands=["calc"])
def calc(conv):
    a = yield "First number?"
    b = yield "Second number?"
    conv.reply(f"Sum: {int(a) + int(b)}")
```

### 16.8 When to use conversation vs FSM

| Use conversation for | Use FSM for |
|---|---|
| Linear dialogs (register, order, survey) | Complex branching with many states |
| Short flows (2-5 steps) | Long flows (10+ states) |
| Everything in one place is easier | States that other handlers need to check |
| Rapid prototyping | Persistent state across restarts |

Both work. Pick the one that makes your code shorter.

### 16.9 Limitations

- **In-memory only.** Conversations are stored in a dict, keyed by
  `(chat_id, user_id)`. If the bot restarts, all active conversations
  are lost. This is a deliberate trade-off: Python generators cannot
  be serialized, so persisting a mid-conversation state would require
  a fundamentally different design (state machine, not generator).

  If you need a dialog that survives restarts, use **FSM** with
  `FileStorage` or `SQLiteStorage` instead.

- **One conversation per user.** A user cannot start a second
  conversation while one is active. Send `/cancel` first.

- **No nested conversations.** Calling `conv` from inside another
  `conv` is not supported. Restructure the flow as a single generator
  with branching.

---

## 17. Further reading

### Python

- Official tutorial: https://docs.python.org/3/tutorial/
- PEP 8 (style guide): https://peps.python.org/pep-0008/
- Real Python: https://realpython.com/

### Telegram

- Bot API reference: https://core.telegram.org/bots/api
- Bot features: https://core.telegram.org/bots/features
- Payment: https://core.telegram.org/bots/payments

### HTTP and networking

- MDN HTTP: https://developer.mozilla.org/en-US/docs/Web/HTTP
- HTTP/2 explained: https://http2-explained.haxx.se/

### Async (when you are ready)

- `asyncio` docs: https://docs.python.org/3/library/asyncio.html
- `aiohttp`: https://docs.aiohttp.org/

### Design patterns

- `aiogram` source: https://github.com/aiogram/aiogram
- `python-telegram-bot`: https://github.com/python-telegram-bot/python-telegram-bot
- Flask, FastAPI — read how decorators and middleware work there

---

## Appendix A — Why zeed exists

Most Telegram Python libraries use `requests` or `aiohttp`:

| Library | Stack | Pros | Cons |
|---|---|---|---|
| `pyTelegramBotAPI` | `requests` | Simple, sync | Extra layers, larger deps |
| `aiogram` | `aiohttp` | Fast, async | Steep curve, heavy |
| `python-telegram-bot` | `httpx` | Feature-rich | Large, complex |
| **`zeed`** | **`urllib3`** | **Lean, direct, secure** | **Young, fewer features** |

`zeed` uses `urllib3.PoolManager` directly — the same layer `requests`
wraps. Skipping `requests` cuts dependencies and per-call overhead.
Sending JSON instead of form data is faster to serialize. Built-in
security is a bonus nobody else ships.

## Appendix B — Glossary

- **Update** — a JSON event from Telegram
- **Handler** — your function that handles an update
- **Filter** — a predicate deciding if a handler runs
- **FSM** — state machine for multi-step dialogs
- **Middleware** — interceptor between dispatch and handler
- **Webhook** — Telegram pushes updates to your URL
- **Long-polling** — you pull updates from Telegram
- **Offset** — id of the last processed update
- **Token** — secret string authenticating your bot
- **Callback data** — string attached to an inline button click (max 64 bytes)

## Appendix C — Cheat sheet

```python
from zeed import Bot, Command, State, StatesGroup

bot = Bot("TOKEN", parse_mode="HTML")

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "Hi!")

@bot.message_handler(Command("help") | Command("h"))
def help_(msg):
    bot.send_message(msg.chat.id, "Commands: /start /help")

@bot.callback_query_handler(func=lambda q: q.data == "ok")
def on_ok(q):
    bot.answer_callback_query(q.id, text="👍")
    bot.edit_message_text("Confirmed", chat_id=q.message.chat.id,
                          message_id=q.message.message_id)

@bot.message_handler(content_types=["photo"])
def photo(msg):
    file_id = msg.photo[-1]["file_id"]
    bot.send_message(msg.chat.id, f"Got photo: {file_id}")

bot.run_polling(timeout=30, workers=2)
```

---

**End of ABOUT.md. Now go build something.**
