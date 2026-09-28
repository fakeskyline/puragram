from zeed import Command, ContentTypes, CallbackData, Regexp, Text
from zeed.types import CallbackQuery, Message


def _msg(text=None, **extra):
    d = {"message_id": 1, "date": 0,
         "chat": {"id": 1, "type": "private"}}
    if text is not None:
        d["text"] = text
    d.update(extra)
    return Message.from_dict(d)


def test_command():
    f = Command("start", "help")
    assert f(_msg("/start"))
    assert f(_msg("/start@mybot"))
    assert f(_msg("/help"))
    assert not f(_msg("/other"))
    assert not f(_msg("no slash"))


def test_text_ignore_case():
    f = Text("Hello", "Hi")
    assert f(_msg("hello"))
    assert f(_msg("HI"))
    assert not f(_msg("hey"))


def test_content_types():
    assert ContentTypes("text")(_msg("hi"))
    assert not ContentTypes("text")(_msg(**{"photo": [{"file_id": "x"}]}))


def test_regexp():
    f = Regexp(r"^\d+$")
    assert f(_msg("12345"))
    assert not f(_msg("12a"))


def test_and_or_not():
    cmd, txt = Command("start"), Text("/start")
    assert (cmd & txt)(_msg("/start"))
    assert (cmd | Text("hi"))(_msg("hi"))
    assert (~cmd)(_msg("hi"))


def test_callback_data():
    f = CallbackData("yes", "no")
    q = CallbackQuery.from_dict({
        "id": "1", "data": "yes",
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
    })
    assert f(q)


def test_regexp_dos_protection():
    import pytest
    with pytest.raises(ValueError):
        Regexp("(a+)+$")