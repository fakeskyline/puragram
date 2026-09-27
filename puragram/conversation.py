"""Multi-step conversations using Python generators.

Example:
    @bot.conversation(commands=["start"], timeout=300)
    def reg(conv):
        name = yield "What's your name?"
        age = yield f"Hi {name}! How old are you?"
        conv.reply(f"Nice to meet you, {name} ({age})!")
"""
import inspect
import threading
import time

from .logger import get_logger

log = get_logger("puragram.conversation")


class _ConversationCancelled(Exception):
    """Raised internally when a conversation is cancelled."""

    def __init__(self, message=None):
        self.message = message
        super().__init__(message or "Cancelled.")


class ConversationCancelled(Exception):
    """Raise inside a conversation to stop it and notify the user."""

    def __init__(self, message=None):
        self.message = message


class ConversationContext:
    """Passed to the conversation function as the first argument."""

    def __init__(self, bot, chat_id, user_id):
        self.bot = bot
        self.chat_id = chat_id
        self.user_id = user_id
        self.data = {}
        self._cancelled = False

    def reply(self, text, **kwargs):
        """Send a message immediately (do not yield)."""
        return self.bot.send_message(self.chat_id, text, **kwargs)

    def cancel(self, message=None):
        """Stop the conversation and optionally notify the user."""
        self._cancelled = True
        raise _ConversationCancelled(message)


class _ActiveConversation:
    __slots__ = ("generator", "context", "started_at", "timeout", "name")

    def __init__(self, generator, context, timeout, name):
        self.generator = generator
        self.context = context
        self.started_at = time.monotonic()
        self.timeout = timeout
        self.name = name

    def expired(self):
        if self.timeout is None:
            return False
        return time.monotonic() - self.started_at > self.timeout

    def touch(self):
        self.started_at = time.monotonic()


class _ConversationEntry:
    __slots__ = ("entry_filter", "timeout", "func", "name")

    def __init__(self, entry_filter, timeout, func, name):
        self.entry_filter = entry_filter
        self.timeout = timeout
        self.func = func
        self.name = name


class ConversationManager:
    """Stores active conversations and routes incoming messages."""

    def __init__(self, bot, default_timeout=300):
        self.bot = bot
        self.default_timeout = default_timeout
        self._entries = []
        self._active = {}
        self._lock = threading.RLock()

    @property
    def has_entries(self):
        return bool(self._entries)

    def add_entry(self, entry_filter, timeout, func):
        self._entries.append(
            _ConversationEntry(entry_filter, timeout, func, func.__name__)
        )
        return func

    def entries(self):
        """Return a snapshot of registered entries."""
        with self._lock:
            return list(self._entries)

    @staticmethod
    def _key(event):
        chat = getattr(event, "chat", None)
        user = getattr(event, "from_user", None)
        cid = chat.id if chat else 0
        uid = user.id if user else 0
        return (cid, uid)

    def has_active(self, event):
        key = self._key(event)
        with self._lock:
            conv = self._active.get(key)
            if conv is None:
                return False
            if conv.expired():
                log.info("conversation %s expired for %s", conv.name, key)
                self._active.pop(key, None)
                return False
            return True

    def start(self, event, entry):
        """Start a new conversation by running the generator to the first yield."""
        key = self._key(event)
        chat_id = event.chat.id if getattr(event, "chat", None) else 0
        user_id = event.from_user.id if getattr(event, "from_user", None) else 0
        ctx = ConversationContext(self.bot, chat_id, user_id)

        try:
            gen = entry.func(ctx)
        except TypeError:
            log.exception("conversation %s: function must be a generator", entry.name)
            return

        if not inspect.isgenerator(gen):
            log.warning("conversation %s: function is not a generator", entry.name)
            return

        timeout = entry.timeout if entry.timeout is not None else self.default_timeout

        try:
            first = next(gen)
        except _ConversationCancelled as e:
            self._notify_cancel(ctx, e)
            return
        except StopIteration:
            return
        except Exception:
            log.exception("conversation %s: failed on start", entry.name)
            return

        with self._lock:
            self._active[key] = _ActiveConversation(gen, ctx, timeout, entry.name)

        if first:
            self.bot.send_message(chat_id, first)

    def resume(self, event):
        """Feed the incoming text into the active conversation's generator."""
        key = self._key(event)
        with self._lock:
            conv = self._active.get(key)
            if conv is None or conv.expired():
                self._active.pop(key, None)
                return False

        text = getattr(event, "text", None) or getattr(event, "caption", None) or ""

        try:
            nxt = conv.generator.send(text)
            conv.touch()
            if nxt:
                self.bot.send_message(conv.context.chat_id, nxt)
            return True
        except _ConversationCancelled as e:
            self._drop(key)
            self._notify_cancel(conv.context, e)
            return True
        except StopIteration:
            self._drop(key)
            return True
        except Exception:
            log.exception("conversation %s failed", conv.name)
            self._drop(key)
            try:
                self.bot.send_message(
                    conv.context.chat_id,
                    "An error occurred. Conversation cancelled.",
                )
            except Exception:
                pass
            return True

    def cancel(self, event, message="Cancelled."):
        """Force-stop the conversation for this user."""
        key = self._key(event)
        with self._lock:
            existed = self._active.pop(key, None) is not None
        if existed and message:
            chat_id = event.chat.id if getattr(event, "chat", None) else 0
            try:
                self.bot.send_message(chat_id, message)
            except Exception:
                pass
        return existed

    def _drop(self, key):
        with self._lock:
            self._active.pop(key, None)

    @staticmethod
    def _notify_cancel(ctx, exc):
        msg = getattr(exc, "message", None)
        if not msg:
            msg = str(exc) or "Cancelled."
        try:
            ctx.bot.send_message(ctx.chat_id, msg)
        except Exception:
            pass