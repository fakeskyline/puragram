# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] — 2026-09-27

### Added

- Inline mode: `@bot.inline_query_handler()` and `bot.answer_inline_query()`
- `InlineQueryResultArticle` and `InlineQueryResultPhoto` result types
- New Bot methods: `send_poll`, `send_location`, `send_contact`, `send_dice`, `send_sticker`
- `send_long_message` — auto-splits long messages using `split_message`
- `CallbackDataPrefix` filter for prefix-matching callback data
- `CallbackQuery.message` access helper

### Changed

- Filled `pyproject.toml` with real author and GitHub URLs
- Added badges to README
- Version bumped to 1.1.0

## [1.0.0] — 2026-09-26

### Added

- Initial public release as `puragram`
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