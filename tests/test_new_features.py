from zeed import (
    CallbackDataPrefix, InlineQuery, InlineQueryText,
    InlineQueryResultArticle, InlineQueryResultPhoto,
    InlineQueryResultGif,
)
from zeed.types import CallbackQuery


def _cb(data):
    return CallbackQuery.from_dict({
        "id": "1",
        "data": data,
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
    })


def _iq(query):
    return InlineQuery.from_dict({
        "id": "q1",
        "query": query,
        "offset": "",
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
    })


# ─── CallbackDataPrefix ───

def test_callback_data_prefix_match():
    f = CallbackDataPrefix("menu:")
    assert f(_cb("menu:start"))
    assert f(_cb("menu:help"))
    assert f(_cb("menu:"))


def test_callback_data_prefix_no_match():
    f = CallbackDataPrefix("menu:")
    assert not f(_cb("btn:start"))
    assert not f(_cb(""))


def test_callback_data_prefix_multiple():
    f = CallbackDataPrefix("menu:", "nav:")
    assert f(_cb("menu:x"))
    assert f(_cb("nav:y"))
    assert not f(_cb("other:z"))


def test_callback_data_prefix_none_data():
    f = CallbackDataPrefix("menu:")
    q = CallbackQuery.from_dict({
        "id": "1",
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
    })
    assert not f(q)


def test_callback_data_prefix_requires_arg():
    import pytest
    with pytest.raises(ValueError):
        CallbackDataPrefix()


# ─── InlineQueryText ───

def test_inline_query_text_match():
    f = InlineQueryText("hello")
    assert f(_iq("hello"))
    assert f(_iq("HELLO"))


def test_inline_query_text_no_match():
    f = InlineQueryText("hello")
    assert not f(_iq("world"))


def test_inline_query_text_case_sensitive():
    f = InlineQueryText("hello", ignore_case=False)
    assert f(_iq("hello"))
    assert not f(_iq("HELLO"))


# ─── InlineQuery parsing ───

def test_inline_query_from_dict():
    q = InlineQuery.from_dict({
        "id": "abc",
        "query": "test",
        "offset": "10",
        "from": {"id": 5, "is_bot": False, "first_name": "Bob"},
    })
    assert q.id == "abc"
    assert q.query == "test"
    assert q.offset == "10"
    assert q.from_user.id == 5


def test_inline_query_from_attr():
    q = InlineQuery.from_dict({
        "id": "abc",
        "query": "test",
        "offset": "",
        "from": {"id": 5, "is_bot": False, "first_name": "Bob"},
    })
    assert q.from_["first_name"] == "Bob"


# ─── InlineQueryResult serialization ───

def test_article_to_dict():
    r = InlineQueryResultArticle(
        id="1",
        title="Test",
        input_message_content={"message_text": "Hello"},
        description="A test result",
    )
    d = r.to_dict()
    assert d["type"] == "article"
    assert d["id"] == "1"
    assert d["title"] == "Test"
    assert d["input_message_content"]["message_text"] == "Hello"
    assert d["description"] == "A test result"
    assert "thumbnail_url" not in d


def test_article_minimal():
    r = InlineQueryResultArticle(
        id="1",
        title="Test",
        input_message_content={"message_text": "Hello"},
    )
    d = r.to_dict()
    assert d["type"] == "article"
    assert "description" not in d


def test_photo_to_dict():
    r = InlineQueryResultPhoto(
        id="2",
        photo_url="https://example.com/photo.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        title="A photo",
    )
    d = r.to_dict()
    assert d["type"] == "photo"
    assert d["photo_url"] == "https://example.com/photo.jpg"
    assert d["thumbnail_url"] == "https://example.com/thumb.jpg"
    assert d["title"] == "A photo"


def test_gif_to_dict():
    r = InlineQueryResultGif(
        id="3",
        gif_url="https://example.com/a.gif",
        thumbnail_url="https://example.com/t.jpg",
    )
    d = r.to_dict()
    assert d["type"] == "gif"
    assert d["gif_url"] == "https://example.com/a.gif"
    assert d["thumbnail_url"] == "https://example.com/t.jpg"
    assert "title" not in d


# ─── Update with inline_query ───

def test_update_parses_inline_query():
    from zeed import Update
    u = Update.from_dict({
        "update_id": 1,
        "inline_query": {
            "id": "q",
            "query": "x",
            "offset": "",
            "from": {"id": 1, "is_bot": False, "first_name": "A"},
        },
    })
    assert u.inline_query is not None
    assert u.inline_query.query == "x"


# ─── send_long_message (без сети — проверяем split_message) ───

def test_split_message_for_long_message():
    from zeed import split_message
    text = "a" * 10000
    parts = split_message(text)
    assert len(parts) > 1
    assert all(len(p) <= 4096 for p in parts)