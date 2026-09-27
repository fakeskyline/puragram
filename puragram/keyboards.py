from .security import validate_callback_data
from .exceptions import ValidationError


def _to_dict(obj):
    return obj.to_dict() if hasattr(obj, "to_dict") else obj


class InlineKeyboardButton:
    def __init__(self, text, callback_data=None, url=None, web_app=None,
                 login_url=None, switch_inline_query=None,
                 switch_inline_query_current_chat=None,
                 callback_game=None, pay=None, **extra):
        if not text or not isinstance(text, str):
            raise ValidationError("Button text required")
        self.data = {"text": text[:64]}

        if callback_data is not None:
            validate_callback_data(callback_data)
            self.data["callback_data"] = callback_data
        if url is not None:
            if not (url.startswith("https://") or url.startswith("tg://")):
                raise ValidationError("URL must start with https:// or tg://")
            self.data["url"] = url
        if web_app is not None:
            self.data["web_app"] = web_app
        if login_url is not None:
            self.data["login_url"] = login_url
        if switch_inline_query is not None:
            self.data["switch_inline_query"] = switch_inline_query
        if switch_inline_query_current_chat is not None:
            self.data["switch_inline_query_current_chat"] = \
                switch_inline_query_current_chat
        if callback_game is not None:
            self.data["callback_game"] = callback_game
        if pay is not None:
            self.data["pay"] = pay
        self.data.update(extra)

    def to_dict(self):
        return self.data


class InlineKeyboardMarkup:
    def __init__(self, keyboard=None):
        self.keyboard = list(keyboard or [])

    def add(self, *buttons):
        self.keyboard.append([_to_dict(b) for b in buttons])
        return self

    row = add

    def to_dict(self):
        return {"inline_keyboard": self.keyboard}

    def __iter__(self):
        return iter(self.keyboard)


class KeyboardButton:
    def __init__(self, text, request_contact=None, request_location=None,
                 request_poll=None, web_app=None, **extra):
        if not text:
            raise ValidationError("Button text required")
        self.data = {"text": str(text)[:64]}
        if request_contact is not None:
            self.data["request_contact"] = request_contact
        if request_location is not None:
            self.data["request_location"] = request_location
        if request_poll is not None:
            self.data["request_poll"] = request_poll
        if web_app is not None:
            self.data["web_app"] = web_app
        self.data.update(extra)

    def to_dict(self):
        return self.data


class ReplyKeyboardMarkup:
    def __init__(self, resize_keyboard=True, one_time_keyboard=False,
                 selective=False, input_field_placeholder=None):
        self.keyboard = []
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective
        self.input_field_placeholder = input_field_placeholder

    def add(self, *buttons):
        self.keyboard.append([_to_dict(b) for b in buttons])
        return self

    row = add

    def to_dict(self):
        d = {
            "keyboard": self.keyboard,
            "resize_keyboard": bool(self.resize_keyboard),
            "one_time_keyboard": bool(self.one_time_keyboard),
            "selective": bool(self.selective),
        }
        if self.input_field_placeholder:
            d["input_field_placeholder"] = str(self.input_field_placeholder)[:64]
        return d


class ForceReply:
    def __init__(self, selective=False, input_field_placeholder=None):
        self.selective = selective
        self.input_field_placeholder = input_field_placeholder

    def to_dict(self):
        d = {"force_reply": True, "selective": bool(self.selective)}
        if self.input_field_placeholder:
            d["input_field_placeholder"] = str(self.input_field_placeholder)[:64]
        return d


class RemoveKeyboard:
    def __init__(self, selective=False):
        self.selective = selective

    def to_dict(self):
        return {"remove_keyboard": True, "selective": bool(self.selective)}


class InlineKeyboardBuilder:
    def __init__(self):
        self._rows = []

    def button(self, text, **kwargs):
        self._rows.append([InlineKeyboardButton(text, **kwargs).to_dict()])
        return self

    def add(self, *buttons):
        self._rows.append([_to_dict(b) for b in buttons])
        return self

    def row(self, *buttons):
        return self.add(*buttons)

    def grid(self, buttons, columns=2):
        if columns < 1:
            raise ValidationError("columns must be >= 1")
        row = []
        for b in buttons:
            row.append(_to_dict(b))
            if len(row) == columns:
                self._rows.append(row)
                row = []
        if row:
            self._rows.append(row)
        return self

    def build(self):
        return InlineKeyboardMarkup(self._rows)