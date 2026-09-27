# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

- Benchmarking shows puragram is now more predictable on flaky networks.
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
