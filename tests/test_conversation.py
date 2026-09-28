"""Tests for the conversation handler."""
import pytest

from zeed import (
    Bot,
    ConversationCancelled,
    ConversationContext,
)
from zeed.conversation import ConversationManager
from zeed.types import Message


def _msg(text="", chat_id=1, user_id=1):
    return Message.from_dict({
        "message_id": 1,
        "date": 0,
        "chat": {"id": chat_id, "type": "private"},
        "from": {"id": user_id, "is_bot": False, "first_name": "A"},
        "text": text,
    })


class FakeBot:
    """Minimal Bot replacement — captures sent messages."""

    def __init__(self):
        self.sent = []

    def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))
        return None


# ─── ConversationContext ───

def test_context_reply():
    bot = FakeBot()
    ctx = ConversationContext(bot, chat_id=10, user_id=20)
    ctx.reply("hello")
    assert bot.sent == [(10, "hello")]


def test_context_cancel_raises():
    bot = FakeBot()
    ctx = ConversationContext(bot, chat_id=1, user_id=1)
    with pytest.raises(Exception):
        ctx.cancel("bye")


def test_context_data_dict():
    bot = FakeBot()
    ctx = ConversationContext(bot, 1, 1)
    ctx.data["x"] = 5
    assert ctx.data["x"] == 5


# ─── Manager registration ───

def test_add_entry():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "hi"

    mgr.add_entry(None, 60, flow)
    assert len(mgr.entries()) == 1
    assert mgr.has_entries is True


def test_no_entries_initially():
    bot = FakeBot()
    mgr = ConversationManager(bot)
    assert mgr.has_entries is False
    assert mgr.entries() == []


# ─── Start + resume ───

def test_start_sends_first_question():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "What is your name?"

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    assert bot.sent == [(1, "What is your name?")]


def test_resume_feeds_answer():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        name = yield "Name?"
        conv.reply(f"Hi {name}!")

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    mgr.resume(_msg("Alice"))
    assert bot.sent == [(1, "Name?"), (1, "Hi Alice!")]


def test_multi_step_conversation():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        name = yield "Name?"
        age = yield f"{name}, age?"
        conv.reply(f"{name} is {age}")

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    mgr.resume(_msg("Bob"))
    mgr.resume(_msg("42"))
    assert bot.sent == [
        (1, "Name?"),
        (1, "Bob, age?"),
        (1, "Bob is 42"),
    ]


def test_resume_without_active_returns_false():
    bot = FakeBot()
    mgr = ConversationManager(bot)
    assert mgr.resume(_msg("hello")) is False


def test_conversation_ends_after_stop_iteration():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "only one"

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    # Resume twice — second time generator already exhausted
    mgr.resume(_msg("hi"))
    assert mgr.resume(_msg("hi")) is False


# ─── Isolated per user/chat ───

def test_two_users_isolated():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        name = yield "Name?"
        conv.reply(f"Hi {name}")

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start", chat_id=1, user_id=1), mgr.entries()[0])
    mgr.start(_msg("/start", chat_id=2, user_id=2), mgr.entries()[0])
    mgr.resume(_msg("Alice", chat_id=1, user_id=1))
    mgr.resume(_msg("Bob", chat_id=2, user_id=2))
    assert (1, "Hi Alice") in bot.sent
    assert (2, "Hi Bob") in bot.sent


# ─── Cancel ───

def test_cancel_stops_conversation():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "step 1"
        yield "step 2"

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    assert mgr.has_active(_msg("x")) is True
    mgr.cancel(_msg("x"))
    assert mgr.has_active(_msg("x")) is False


# ─── Generator requirement ───

def test_non_generator_rejected(caplog):
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        return "not a generator"

    entry_filter, timeout, func, name = None, 60, flow, "flow"
    from zeed.conversation import _ConversationEntry
    entry = _ConversationEntry(entry_filter, timeout, func, name)
    mgr.start(_msg("/start"), entry)
    # No messages sent, no crash
    assert bot.sent == []


# ─── ConversationCancelled from inside ───

def test_cancel_from_inside():
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        name = yield "Name?"
        if name == "quit":
            conv.cancel("Bye!")
            return
        conv.reply(f"Hi {name}")

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    mgr.resume(_msg("quit"))
    assert (1, "Bye!") in bot.sent
    assert mgr.has_active(_msg("x")) is False


# ─── Timeout notification ───

def test_timeout_sends_notification(monkeypatch):
    """When a conversation times out, the user gets a message."""
    import time
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "step 1"

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    assert bot.sent == [(1, "step 1")]

    # Fake the timeout by making time.monotonic jump forward
    original = time.monotonic
    fake_now = [original() + 999]

    def fake_monotonic():
        return fake_now[0]

    monkeypatch.setattr(
        "zeed.conversation.time.monotonic", fake_monotonic
    )

    # has_active should detect expiry and notify
    assert mgr.has_active(_msg("hello")) is False
    assert (1, "Dialog timed out. Send the command again to restart.") in bot.sent


def test_timeout_clears_active(monkeypatch):
    """After timeout, the conversation slot is free for a new one."""
    import time
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "step 1"

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])

    fake_now = [time.monotonic() + 999]
    monkeypatch.setattr(
        "zeed.conversation.time.monotonic", lambda: fake_now[0]
    )

    mgr.has_active(_msg("x"))  # triggers cleanup
    # Now the slot is free
    assert mgr.has_active(_msg("x")) is False


# ─── /cancel edge cases ───

def test_cancel_outside_conversation():
    """Calling /cancel when no conversation is active should not crash."""
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "step 1"

    mgr.add_entry(None, 60, flow)
    # No active conversation
    result = mgr.cancel(_msg("/cancel"))
    assert result is False
    assert bot.sent == []


def test_cancel_sends_custom_message():
    """Cancelling sends the provided message to the user."""
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "step 1"

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    bot.sent.clear()

    mgr.cancel(_msg("/cancel"), message="Stopped by /cancel.")
    assert bot.sent == [(1, "Stopped by /cancel.")]


def test_cancel_and_restart():
    """After cancel, a new conversation can start for the same user."""
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        name = yield "Name?"
        conv.reply(f"Hi {name}")

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    mgr.cancel(_msg("/cancel"))
    assert mgr.has_active(_msg("x")) is False

    # Start again
    bot.sent.clear()
    mgr.start(_msg("/start"), mgr.entries()[0])
    assert bot.sent == [(1, "Name?")]


def test_cancel_from_second_step():
    """Cancel works from any step of the conversation."""
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        a = yield "Step 1?"
        b = yield f"Got {a}. Step 2?"
        conv.reply(f"Done: {a}, {b}")

    mgr.add_entry(None, 60, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])
    mgr.resume(_msg("first"))
    # Now at step 2
    assert mgr.has_active(_msg("x")) is True
    mgr.cancel(_msg("/cancel"))
    assert mgr.has_active(_msg("x")) is False


def test_cancel_message_not_sent_when_no_active():
    """If no active conversation, cancel does not send anything."""
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "x"

    mgr.add_entry(None, 60, flow)
    result = mgr.cancel(_msg("/cancel"), message="Nothing to cancel.")
    assert result is False
    assert bot.sent == []


# ─── Timeout=None disables the timeout ───

def test_no_timeout_does_not_expire(monkeypatch):
    import time
    bot = FakeBot()
    mgr = ConversationManager(bot)

    def flow(conv):
        yield "step 1"

    mgr.add_entry(None, None, flow)
    mgr.start(_msg("/start"), mgr.entries()[0])

    fake_now = [time.monotonic() + 99999]
    monkeypatch.setattr(
        "zeed.conversation.time.monotonic", lambda: fake_now[0]
    )

    assert mgr.has_active(_msg("x")) is True