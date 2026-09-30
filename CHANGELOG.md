# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.3.0] — 2026-09-30

### Added — Bot API 9.0–10.3 support

- **Managed bots**: `get_managed_bot_token`, `replace_managed_bot_token`
- **Checklists**: `send_checklist`, `edit_message_checklist`,
  `Checklist`, `ChecklistTask` classes
- **Topics in private chats**: `has_topics_enabled` in `User`
- **Colored buttons and custom emoji**: `style` and
  `icon_custom_emoji_id` in `InlineKeyboardButton` and `KeyboardButton`
- **Message streaming**: `send_message_draft` for ChatGPT-style
  character-by-character output
- **Rich Messages**: `send_rich_message`, `RichMessageBlock` class
- **Ephemeral messages**: `send_ephemeral_message` — visible only to
  a specific user, disappears after reading
- **Guest mode**: `guest_message_handler` for handling guest messages
- New `guest_message` field in `Update`
- New `ephemeral` flag in `Message`

### Changed

- Version bumped to 1.3.0

### Notes

- All new features are opt-in. Existing code works unchanged.

## [1.2.2] — 2026-09-28

### Changed

- Renamed from `puragram` to `zeed` to avoid confusion with the unrelated
  `puregram` package. The API is unchanged.
- New PyPI: https://pypi.org/project/zeed/
- New GitHub: https://github.com/fakeskyline/zeed

## [1.2.1] — 2026-09-27

### Fixed

- **Timeout notification** — when a conversation expires, the user now
  receives `Dialog timed out. Send the command again to restart.`
  instead of silence.
- **`timeout=None`** now correctly disables the timeout. Previously it
  fell back to the default 300 seconds, so long-running dialogs
  (surveys, multi-hour forms) were cancelled unexpectedly.

### Added

- 7 more tests for `/cancel` and timeout edge cases:
  - cancel outside an active conversation
  - cancel with custom message
  - cancel from any step
  - cancel and restart the same user
  - timeout sends notification
  - timeout clears the slot
  - `timeout=None` disables expiry

### Notes

- Total test count: 105.

## [1.2.0] — 2026-09-27

### Added

- **Conversation handler** — multi-step dialogs via Python generators:

  ```python
  @bot.conversation(commands=["start"], timeout=300)
  def reg(conv):
      name = yield "What's your name?"
      age = yield f"Hi {name}! How old are you?"
      conv.reply(f"Nice to meet you, {name} ({age})!")
```

· /cancel command automatically stops an active conversation
· ConversationContext — access to bot, chat_id, user_id, data,
  reply(), cancel()
· ConversationCancelled exception — raise inside a conversation to
  stop it cleanly and notify the user
· Configurable timeout per conversation (default 300 seconds)

Notes

· Conversations are stored in memory only. Restarting the bot cancels
  all active conversations.

## [1.1.2] — 2026-09-27

### Changed

- `pyproject.toml` now uses the SPDX license format:
  `license = "MIT"` and `license-files = ["LICENSE"]`
- Removed the deprecated `License :: OSI Approved :: MIT License` classifier
- Documentation refresh: `README.md` and `ABOUT.md` updated to 1.1.2
  with inline mode, new methods, performance benchmarks, and security notes

### Notes

- No code changes. Behavior is identical to 1.1.1.
- This release only silences the setuptools deprecation warnings that
  appeared during builds.

## [1.1.1] — 2026-09-27

### Changed

- **Stability improvements** in `TelegramAPI`:
  - `PoolManager(block=True)` — reuse connections instead of opening new ones
  - `TCP_NODELAY` enabled — disables Nagle's algorithm for lower latency
  - `SO_KEEPALIVE` enabled — keeps connections alive
  - Separate `connect_timeout` (5s) and read timeout (30s)
  - `retries=0` by default — no hidden retry delays on HTTP status codes
  - `pool_size` default raised from 10 to 16

### Notes

- Benchmarking shows zeed is now more predictable on flaky networks.
  For applications that need retry on connection failures, pass
  `Bot(..., retries=2)` explicitly.

## [1.1.0] — 2026-09-27

### Added

- Inline mode: `@inline_query_handler()` and `bot.answer_inline_query()`
- `InlineQueryResultArticle`, `InlineQueryResultPhoto`, `InlineQueryResultGif`
- New Bot methods: `send_poll`, `send_location`, `send_contact`, `send_dice`, `send_sticker`
- `send_long_message` — auto-splits long messages using `split_message`
- `CallbackDataPrefix` filter for prefix-matching callback data
- `InlineQueryText` filter for inline query text

### Changed

- Filled `pyproject.toml` with real author and GitHub URLs
- Added badges to README
- Version bumped to 1.1.0

## [1.0.0] — 2026-09-26

### Added

- Initial public release as `zeed`
- `Bot` with polling and dispatch
- Handlers: message, edited_message, channel_post, edited_channel_post, callback_query
- Filters: Command, Text, Regexp, ContentTypes, ChatType, ChatId, UserId, CallbackData, Func
- FSM: State, StatesGroup, FSMContext, MemoryStorage, FileStorage, SQLiteStorage
- Middleware: LoggingMiddleware, ThrottlingMiddleware, TimingMiddleware
- Webhook server on stdlib `http.server`
- Security: path traversal, size limits, ReDoS protection, token redaction, dedup
- Keyboard classes and builders
- Multithreaded polling via `workers=N`
- File sending: photo, document, video, audio, voice
