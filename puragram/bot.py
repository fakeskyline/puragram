import inspect
import io
import os
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from .api import TelegramAPI
from .exceptions import TelegramError, SecurityError
from .filters import _ensure as _ensure_filter, build_named
from .fsm import FSMContext, MemoryStorage
from .conversation import ConversationManager
from .logger import get_logger
from .security import safe_path, check_size, validate_text
from .types import Message, Update, User
from .utils import split_message

log = get_logger("puragram")


class _DedupCache:
    def __init__(self, max_size=1024):
        self.max_size = max_size
        self._seen = OrderedDict()
        self._lock = threading.Lock()

    def seen(self, update_id):
        with self._lock:
            if update_id in self._seen:
                self._seen.move_to_end(update_id)
                return True
            self._seen[update_id] = True
            if len(self._seen) > self.max_size:
                self._seen.popitem(last=False)
            return False


def _open_file(source, base_dir=None):
    if hasattr(source, "read"):
        return source, False

    if isinstance(source, (bytes, bytearray)):
        if len(source) > 50 * 1024 * 1024:
            raise SecurityError("Bytes too large for upload")
        return io.BytesIO(bytes(source)), True

    if isinstance(source, str):
        if source.startswith(("http://", "https://")):
            return None, False
        if os.path.isfile(source):
            p = safe_path(source, base_dir=base_dir, must_exist=True)
            check_size(p)
            return open(p, "rb"), True
        return None, False

    return None, False


class _Handler:
    __slots__ = ("kind", "func", "filter", "state", "_wants_data")

    def __init__(self, kind, func, filter_=None, state=None):
        self.kind = kind
        self.func = func
        self.filter = filter_
        self.state = str(state) if state is not None else None
        try:
            params = inspect.signature(func).parameters
            self._wants_data = len(params) >= 2
        except (TypeError, ValueError):
            self._wants_data = False

    def invoke(self, event, data):
        if self._wants_data:
            return self.func(event, data)
        return self.func(event)


class Bot:
    def __init__(self, token, parse_mode=None, disable_web_page_preview=None,
                 pool_size=16, timeout=30.0, retries=0, storage=None,
                 file_base_dir=None, allowed_updates=None,
                 connect_timeout=5.0):
        self.token = token
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.api = TelegramAPI(
            token,
            pool_size=pool_size,
            timeout=timeout,
            connect_timeout=connect_timeout,
            retries=retries,
        )
        self.fsm_storage = storage or MemoryStorage()
        self.file_base_dir = file_base_dir
        self._handlers = []
        self._middlewares = []
        self._offset = None
        self._running = False
        self._me = None
        self._executor = None
        self._dedup = _DedupCache()
        self._allowed_updates_override = allowed_updates
        self.conversations = ConversationManager(self)

    # ─────────── Реєстрація хендлерів ───────────

    def _register(self, kind, custom_filters, state, named):
        f = build_named(**named)
        for cf in custom_filters:
            cf = _ensure_filter(cf)
            f = cf if f is None else (f & cf)

        def deco(func):
            self._handlers.append(_Handler(kind, func, f, state))
            return func
        return deco

    def message_handler(self, *filters, state=None, **named):
        return self._register("message", filters, state, named)

    def edited_message_handler(self, *filters, state=None, **named):
        return self._register("edited_message", filters, state, named)

    def channel_post_handler(self, *filters, state=None, **named):
        return self._register("channel_post", filters, state, named)

    def edited_channel_post_handler(self, *filters, state=None, **named):
        return self._register("edited_channel_post", filters, state, named)

    def callback_query_handler(self, *filters, state=None, **named):
        return self._register("callback_query", filters, state, named)

    def inline_query_handler(self, *filters, state=None, **named):
        return self._register("inline_query", filters, state, named)

    def conversation(self, *filters, timeout=300, **named):
        """Register a conversation entry point.

        Usage:
            @bot.conversation(commands=["start"], timeout=300)
            def reg(conv):
                name = yield "Your name?"
                conv.reply(f"Hi {name}!")
        """
        f = build_named(**named)
        for cf in filters:
            cf = _ensure_filter(cf)
            f = cf if f is None else (f & cf)

        def deco(func):
            self.conversations.add_entry(f, timeout, func)
            return func
        return deco

    def middleware(self, mw):
        self._middlewares.append(mw)
        return mw

    # ─────────── API методи ───────────

    def _defaults(self, kwargs):
        if self.parse_mode and "parse_mode" not in kwargs:
            kwargs["parse_mode"] = self.parse_mode
        if (self.disable_web_page_preview is not None
                and "disable_web_page_preview" not in kwargs):
            kwargs["disable_web_page_preview"] = self.disable_web_page_preview
        rm = kwargs.get("reply_markup")
        if rm is not None and hasattr(rm, "to_dict"):
            kwargs["reply_markup"] = rm.to_dict()
        return kwargs

    def send_message(self, chat_id, text, **kwargs):
        validate_text(text)
        return Message.from_dict(self.api.call(
            "send_message", **self._defaults(
                {"chat_id": chat_id, "text": text, **kwargs}
            )
        ))

    def send_long_message(self, chat_id, text, **kwargs):
        """Splits long text into chunks and sends each. Returns list of Message."""
        validate_text(text)
        chunks = split_message(text)
        results = []
        for chunk in chunks:
            results.append(self.send_message(chat_id, chunk, **kwargs))
        return results

    def edit_message_text(self, text, chat_id=None, message_id=None,
                          inline_message_id=None, **kwargs):
        validate_text(text)
        params = self._defaults({"text": text, **kwargs})
        if chat_id is not None:
            params["chat_id"] = chat_id
        if message_id is not None:
            params["message_id"] = message_id
        if inline_message_id is not None:
            params["inline_message_id"] = inline_message_id
        res = self.api.call("edit_message_text", **params)
        return Message.from_dict(res) if isinstance(res, dict) else res

    def edit_message_reply_markup(self, chat_id=None, message_id=None,
                                  inline_message_id=None, reply_markup=None):
        params = {}
        if chat_id is not None:
            params["chat_id"] = chat_id
        if message_id is not None:
            params["message_id"] = message_id
        if inline_message_id is not None:
            params["inline_message_id"] = inline_message_id
        if reply_markup is not None:
            params["reply_markup"] = (reply_markup.to_dict()
                                      if hasattr(reply_markup, "to_dict")
                                      else reply_markup)
        return self.api.call("edit_message_reply_markup", **params)

    def delete_message(self, chat_id, message_id):
        return self.api.call("delete_message",
                             chat_id=chat_id, message_id=message_id)

    def send_chat_action(self, chat_id, action):
        return self.api.call("send_chat_action",
                             chat_id=chat_id, action=action)

    def answer_callback_query(self, callback_query_id, text=None,
                              show_alert=False, url=None, cache_time=None):
        params = {"callback_query_id": callback_query_id}
        if text is not None:
            validate_text(text, limit=200)
            params["text"] = text
        if show_alert:
            params["show_alert"] = True
        if url is not None:
            params["url"] = url
        if cache_time is not None:
            params["cache_time"] = int(cache_time)
        return self.api.call("answer_callback_query", **params)

    def answer_inline_query(self, inline_query_id, results,
                            cache_time=300, is_personal=False,
                            next_offset=None, button=None):
        """Answers an inline query with results.

        `results` is a list of objects with to_dict() (e.g. InlineQueryResultArticle)
        or plain dicts.
        """
        serialized = [
            r.to_dict() if hasattr(r, "to_dict") else r for r in results
        ]
        params = {
            "inline_query_id": inline_query_id,
            "results": serialized,
            "cache_time": int(cache_time),
            "is_personal": bool(is_personal),
        }
        if next_offset is not None:
            params["next_offset"] = next_offset
        if button is not None:
            params["button"] = (button.to_dict()
                                if hasattr(button, "to_dict") else button)
        return self.api.call("answer_inline_query", **params)

    def get_me(self):
        if self._me is None:
            self._me = User.from_dict(self.api.call("get_me"))
        return self._me

    def get_updates(self, timeout=0, allowed_updates=None):
        return self.api.call(
            "getUpdates",
            offset=self._offset,
            timeout=timeout,
            allowed_updates=allowed_updates,
        )

    def set_webhook(self, url, **kwargs):
        return self.api.call("set_webhook", url=url, **kwargs)

    def delete_webhook(self, drop_pending_updates=False):
        return self.api.call("delete_webhook",
                             drop_pending_updates=drop_pending_updates)

    def call(self, method, **params):
        return self.api.call(method, **params)

    # ─────────── Файли ───────────

    def _send_file(self, method, chat_id, field_name, source,
                   caption=None, **kwargs):
        params = self._defaults({"chat_id": chat_id, **kwargs})
        if caption is not None:
            validate_text(caption, limit=1024)
            params["caption"] = caption
        fp, close = _open_file(source, base_dir=self.file_base_dir)
        try:
            if fp is None:
                params[field_name] = source
                return Message.from_dict(self.api.call(method, **params))
            return Message.from_dict(self.api.call(
                method, files={field_name: fp}, **params
            ))
        finally:
            if close and fp is not None:
                fp.close()

    def send_photo(self, chat_id, photo, caption=None, **kwargs):
        return self._send_file("send_photo", chat_id, "photo", photo,
                               caption=caption, **kwargs)

    def send_document(self, chat_id, document, caption=None, **kwargs):
        return self._send_file("send_document", chat_id, "document",
                               document, caption=caption, **kwargs)

    def send_video(self, chat_id, video, caption=None, **kwargs):
        return self._send_file("send_video", chat_id, "video", video,
                               caption=caption, **kwargs)

    def send_audio(self, chat_id, audio, caption=None, **kwargs):
        return self._send_file("send_audio", chat_id, "audio", audio,
                               caption=caption, **kwargs)

    def send_voice(self, chat_id, voice, caption=None, **kwargs):
        return self._send_file("send_voice", chat_id, "voice", voice,
                               caption=caption, **kwargs)

    def send_sticker(self, chat_id, sticker, **kwargs):
        return self._send_file("send_sticker", chat_id, "sticker", sticker,
                               **kwargs)

    # ─────────── Нові методи ───────────

    def send_poll(self, chat_id, question, options, is_anonymous=True,
                  type="regular", allows_multiple_answers=False,
                  correct_option_id=None, explanation=None, **kwargs):
        params = self._defaults({
            "chat_id": chat_id,
            "question": str(question)[:300],
            "options": [{"text": str(o)[:100]} for o in options],
            "is_anonymous": bool(is_anonymous),
            "type": type,
            "allows_multiple_answers": bool(allows_multiple_answers),
            **kwargs,
        })
        if correct_option_id is not None:
            params["correct_option_id"] = int(correct_option_id)
        if explanation is not None:
            params["explanation"] = str(explanation)[:200]
        return Message.from_dict(self.api.call("send_poll", **params))

    def send_location(self, chat_id, latitude, longitude,
                      horizontal_accuracy=None, live_period=None,
                      **kwargs):
        params = self._defaults({
            "chat_id": chat_id,
            "latitude": float(latitude),
            "longitude": float(longitude),
            **kwargs,
        })
        if horizontal_accuracy is not None:
            params["horizontal_accuracy"] = float(horizontal_accuracy)
        if live_period is not None:
            params["live_period"] = int(live_period)
        return Message.from_dict(self.api.call("send_location", **params))

    def send_contact(self, chat_id, phone_number, first_name,
                     last_name=None, vcard=None, **kwargs):
        params = self._defaults({
            "chat_id": chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
            **kwargs,
        })
        if last_name is not None:
            params["last_name"] = last_name
        if vcard is not None:
            params["vcard"] = vcard
        return Message.from_dict(self.api.call("send_contact", **params))

    def send_dice(self, chat_id, emoji=None, **kwargs):
        params = self._defaults({"chat_id": chat_id, **kwargs})
        if emoji is not None:
            params["emoji"] = emoji
        return Message.from_dict(self.api.call("send_dice", **params))

    # ─────────── Polling ───────────

    def polling(self, timeout=30, non_stop=True, interval=0.0,
                allowed_updates=None, drop_pending_updates=False,
                skip_delete_webhook=False, workers=1, dedup=True):
        self._running = True

        if not skip_delete_webhook:
            try:
                self.delete_webhook(drop_pending_updates=drop_pending_updates)
            except TelegramError as e:
                log.warning("delete_webhook: %s", e)

        if allowed_updates is None:
            allowed_updates = (self._allowed_updates_override
                               or self._collect_allowed_updates())

        if workers > 1:
            self._executor = ThreadPoolExecutor(max_workers=workers)

        try:
            while self._running:
                try:
                    updates = self.api.call(
                        "getUpdates",
                        offset=self._offset,
                        timeout=timeout,
                        allowed_updates=allowed_updates,
                    )
                except TelegramError as e:
                    log.error("getUpdates: %s", e)
                    time.sleep(1.0)
                    continue

                for raw in updates:
                    uid = raw.get("update_id")
                    self._offset = uid + 1
                    if dedup and self._dedup.seen(uid):
                        log.debug("skip duplicate update %s", uid)
                        continue
                    upd = Update.from_dict(raw)
                    if self._executor:
                        self._executor.submit(self._dispatch, upd)
                    else:
                        self._dispatch(upd)

                if not non_stop:
                    break
                if interval:
                    time.sleep(interval)

        except KeyboardInterrupt:
            log.info("Received Ctrl+C, stopping polling")
        finally:
            self._running = False
            if self._executor:
                self._executor.shutdown(wait=False)
                self._executor = None

    def run_polling(self, **kwargs):
        try:
            bot_name = "?"
            try:
                bot_name = f"@{self.get_me().username}"
            except Exception:
                pass
            log.info("Bot %s started. Ctrl+C to stop.", bot_name)
            self.polling(**kwargs)
        except KeyboardInterrupt:
            log.info("Stopped by user")
        finally:
            self.close()
            log.info("Connection closed")

    def stop_polling(self):
        self._running = False

    def close(self):
        self.stop_polling()
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        self.api.close()
        if hasattr(self.fsm_storage, "close"):
            self.fsm_storage.close()

    def _collect_allowed_updates(self):
        kinds = {h.kind for h in self._handlers}
        return list(kinds) if kinds else None

    # ─────────── Диспетчер ───────────

    def _dispatch(self, update):
        msg = update.message
        if msg is not None and self.conversations.has_entries:
            text = getattr(msg, "text", None) or ""
            if text.startswith("/cancel"):
                if self.conversations.cancel(msg):
                    return
            if self.conversations.has_active(msg):
                if self.conversations.resume(msg):
                    return
            for entry in self.conversations.entries():
                if entry.entry_filter is None or entry.entry_filter(msg):
                    self.conversations.start(msg, entry)
                    return

        pairs = (
            ("message", update.message),
            ("edited_message", update.edited_message),
            ("channel_post", update.channel_post),
            ("edited_channel_post", update.edited_channel_post),
            ("callback_query", update.callback_query),
            ("inline_query", update.inline_query),
        )
        for kind, obj in pairs:
            if obj is None:
                continue
            for h in self._handlers:
                if h.kind != kind:
                    continue
                if h.filter is not None and not h.filter(obj):
                    continue
                ctx = None
                if h.state is not None:
                    ctx = FSMContext(self.fsm_storage, self._fsm_key(obj))
                    if ctx.get_state() != h.state:
                        continue
                self._invoke(h, obj, ctx)

    @staticmethod
    def _fsm_key(obj):
        chat = getattr(obj, "chat", None)
        user = getattr(obj, "from_user", None)
        cid = chat.id if chat else 0
        uid = user.id if user else 0
        return f"{cid}:{uid}"

    def _invoke(self, handler, event, ctx):
        data = {"bot": self, "state": ctx, "update": event}

        def core(evt, d):
            return handler.invoke(evt, d)

        chain = core
        for mw in reversed(self._middlewares):
            chain = self._wrap(mw, chain)

        try:
            chain(event, data)
        except Exception:
            log.exception("handler %s failed",
                          getattr(handler.func, "__name__", "?"))

    @staticmethod
    def _wrap(mw, inner):
        def wrapped(event, data):
            return mw(inner, event, data)
        return wrapped