# Changelog

## [1.0.0] — 2026-27-09

### Added

- Initial public release
- Bot class with polling and dispatch
- Handlers: message, edited_message, channel_post, edited_channel_post, callback_query
- Filters: Command, Text, Regexp, ContentTypes, ChatType, ChatId, UserId, CallbackData, Func
- FSM: State, StatesGroup, FSMContext, MemoryStorage, FileStorage, SQLiteStorage
- Middleware: LoggingMiddleware, ThrottlingMiddleware, TimingMiddleware
- Webhook server on stdlib http.server with secret token check
- Security: path traversal guard, size limits, callback data validation, ReDoS protection, token redaction, update deduplication
- Utility helpers: escape_html, escape_markdown, split_message, user_mention
- Keyboard classes: InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ForceReply, RemoveKeyboard, InlineKeyboardBuilder
- Multithreaded polling via workers=N
- File sending: send_photo, send_document, send_video, send_audio, send_voice

### Notes

- - Initial public release as puragram.