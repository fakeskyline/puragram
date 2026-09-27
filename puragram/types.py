from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            is_bot=d.get("is_bot", False),
            first_name=d.get("first_name", ""),
            last_name=d.get("last_name"),
            username=d.get("username"),
            language_code=d.get("language_code"),
            raw=d,
        )


@dataclass
class Chat:
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            type=d.get("type", "private"),
            title=d.get("title"),
            username=d.get("username"),
            first_name=d.get("first_name"),
            last_name=d.get("last_name"),
            raw=d,
        )


_CONTENT_TYPES = (
    "text", "audio", "document", "photo", "sticker", "video",
    "video_note", "voice", "location", "contact", "venue",
    "animation", "poll", "dice", "new_chat_members",
    "left_chat_member", "new_chat_title", "new_chat_photo",
    "delete_chat_photo", "group_chat_created",
    "supergroup_chat_created", "channel_chat_created",
    "pinned_message", "invoice", "successful_payment",
    "proximity_alert_triggered", "video_chat_scheduled",
    "video_chat_started", "video_chat_ended",
    "video_chat_participants_invited", "web_app_data",
)


@dataclass
class Message:
    message_id: int
    date: int
    chat: Chat
    from_user: Optional[User] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    entities: Optional[list] = None
    caption_entities: Optional[list] = None
    reply_to_message: Optional["Message"] = None
    raw: dict = field(default_factory=dict)

    @property
    def content_type(self) -> str:
        for ct in _CONTENT_TYPES:
            if self.raw.get(ct) is not None:
                return ct
        return "unknown"

    @classmethod
    def from_dict(cls, d):
        return cls(
            message_id=d["message_id"],
            date=d.get("date", 0),
            chat=Chat.from_dict(d["chat"]),
            from_user=User.from_dict(d["from"]) if "from" in d else None,
            text=d.get("text"),
            caption=d.get("caption"),
            entities=d.get("entities"),
            caption_entities=d.get("caption_entities"),
            reply_to_message=(Message.from_dict(d["reply_to_message"])
                              if "reply_to_message" in d else None),
            raw=d,
        )

    def __getattr__(self, item):
        if item == "from_":
            item = "from"
        raw = self.__dict__.get("raw", {})
        if item in raw:
            return raw[item]
        raise AttributeError(item)


@dataclass
class CallbackQuery:
    id: str
    from_user: Optional[User] = None
    chat_instance: Optional[str] = None
    data: Optional[str] = None
    message: Optional[Message] = None
    inline_message_id: Optional[str] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            from_user=User.from_dict(d["from"]) if "from" in d else None,
            chat_instance=d.get("chat_instance"),
            data=d.get("data"),
            message=Message.from_dict(d["message"]) if "message" in d else None,
            inline_message_id=d.get("inline_message_id"),
            raw=d,
        )

    def __getattr__(self, item):
        if item == "from_":
            item = "from"
        raw = self.__dict__.get("raw", {})
        if item in raw:
            return raw[item]
        raise AttributeError(item)


@dataclass
class Update:
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    channel_post: Optional[Message] = None
    edited_channel_post: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None
    inline_query: Optional[dict] = None
    chosen_inline_result: Optional[dict] = None
    shipping_query: Optional[dict] = None
    pre_checkout_query: Optional[dict] = None
    poll: Optional[dict] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d):
        def _msg(key):
            return Message.from_dict(d[key]) if key in d else None
        return cls(
            update_id=d["update_id"],
            message=_msg("message"),
            edited_message=_msg("edited_message"),
            channel_post=_msg("channel_post"),
            edited_channel_post=_msg("edited_channel_post"),
            callback_query=(CallbackQuery.from_dict(d["callback_query"])
                            if "callback_query" in d else None),
            inline_query=d.get("inline_query"),
            chosen_inline_result=d.get("chosen_inline_result"),
            shipping_query=d.get("shipping_query"),
            pre_checkout_query=d.get("pre_checkout_query"),
            poll=d.get("poll"),
            raw=d,
        )


from .keyboards import (  # noqa: E402, F401
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
    ForceReply, RemoveKeyboard,
)