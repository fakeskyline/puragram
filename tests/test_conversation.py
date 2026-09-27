"""Tests for the conversation handler."""
import pytest

from puragram import (
    Bot,
    ConversationCancelled,
    ConversationContext,
)
from puragram.conversation import ConversationManager
from puragram.types import Message


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
    from puragram.conversation import _ConversationEntry
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