"""Tests for zeed 1.3.0 features (Bot API 9.0-10.3)."""
import pytest

from zeed import (
    Checklist,
    ChecklistTask,
    InlineKeyboardButton,
    KeyboardButton,
    RichMessageBlock,
    User,
    Message,
    Update,
)
from zeed.exceptions import ValidationError


# ─── Colored buttons and custom emoji ───

def test_inline_button_with_style():
    b = InlineKeyboardButton("Click", callback_data="x", style="primary")
    assert b.to_dict()["style"] == "primary"


def test_inline_button_with_emoji():
    b = InlineKeyboardButton("Hi", callback_data="x",
                             icon_custom_emoji_id="5368324170671202286")
    assert b.to_dict()["icon_custom_emoji_id"] == "5368324170671202286"


def test_inline_button_all_styles():
    for s in ("primary", "secondary", "success", "danger"):
        b = InlineKeyboardButton("T", callback_data="x", style=s)
        assert b.to_dict()["style"] == s


def test_inline_button_bad_style():
    with pytest.raises(ValidationError):
        InlineKeyboardButton("T", callback_data="x", style="rainbow")


def test_keyboard_button_with_style():
    b = KeyboardButton("OK", style="success")
    assert b.to_dict()["style"] == "success"


def test_keyboard_button_with_emoji():
    b = KeyboardButton("OK", icon_custom_emoji_id="123")
    assert b.to_dict()["icon_custom_emoji_id"] == "123"


def test_keyboard_button_bad_style():
    with pytest.raises(ValidationError):
        KeyboardButton("OK", style="purple")


# ─── Checklist ───

def test_checklist_task_to_dict():
    t = ChecklistTask(text="Buy milk", is_completed=False)
    assert t.to_dict() == {"text": "Buy milk", "is_completed": False}


def test_checklist_task_from_dict():
    t = ChecklistTask.from_dict({"text": "Do", "is_completed": True})
    assert t.text == "Do"
    assert t.is_completed is True


def test_checklist_to_dict():
    c = Checklist("Todo", [
        ChecklistTask("Task 1"),
        ChecklistTask("Task 2", is_completed=True),
    ])
    d = c.to_dict()
    assert d["title"] == "Todo"
    assert len(d["tasks"]) == 2
    assert d["tasks"][0]["text"] == "Task 1"


def test_checklist_from_dict():
    d = {
        "title": "Shopping",
        "tasks": [
            {"text": "Bread", "is_completed": False},
            {"text": "Eggs", "is_completed": True},
        ],
    }
    c = Checklist.from_dict(d)
    assert c.title == "Shopping"
    assert len(c.tasks) == 2
    assert c.tasks[1].is_completed is True


# ─── Rich Message blocks ───

def test_rich_block_to_dict():
    b = RichMessageBlock(type="paragraph", content={"text": "Hello"})
    assert b.to_dict() == {"type": "paragraph", "text": "Hello"}


def test_rich_block_from_dict():
    b = RichMessageBlock.from_dict({"type": "heading", "text": "Title"})
    assert b.type == "heading"
    assert b.content["text"] == "Title"


def test_rich_block_default_type():
    b = RichMessageBlock.from_dict({"text": "No type"})
    assert b.type == "paragraph"


# ─── User: has_topics_enabled ───

def test_user_has_topics_enabled():
    u = User.from_dict({
        "id": 1, "is_bot": False, "first_name": "A",
        "has_topics_enabled": True,
    })
    assert u.has_topics_enabled is True


def test_user_has_topics_default_false():
    u = User.from_dict({"id": 1, "is_bot": False, "first_name": "A"})
    assert u.has_topics_enabled is False


def test_user_is_premium():
    u = User.from_dict({
        "id": 1, "is_bot": False, "first_name": "A",
        "is_premium": True,
    })
    assert u.is_premium is True


# ─── Message: ephemeral ───

def test_message_ephemeral_flag():
    m = Message.from_dict({
        "message_id": 1, "date": 0,
        "chat": {"id": 1, "type": "private"},
        "text": "hi", "ephemeral": True,
    })
    assert m.ephemeral is True


def test_message_ephemeral_default():
    m = Message.from_dict({
        "message_id": 1, "date": 0,
        "chat": {"id": 1, "type": "private"},
        "text": "hi",
    })
    assert m.ephemeral is False


# ─── Update: guest_message ───

def test_update_guest_message_field():
    u = Update.from_dict({
        "update_id": 1,
        "guest_message": {"id": "g1", "text": "hi"},
    })
    assert u.guest_message is not None
    assert u.guest_message["text"] == "hi"


def test_update_without_guest_message():
    u = Update.from_dict({
        "update_id": 1,
        "message": {
            "message_id": 1, "date": 0,
            "chat": {"id": 1, "type": "private"},
            "text": "hi",
        },
    })
    assert u.guest_message is None


# ─── Chat: is_forum ───

def test_chat_is_forum():
    m = Message.from_dict({
        "message_id": 1, "date": 0,
        "chat": {"id": 1, "type": "supergroup", "is_forum": True},
        "text": "hi",
    })
    assert m.chat.is_forum is True
