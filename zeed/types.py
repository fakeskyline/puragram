"""Telegram types with support for recent Bot API additions."""

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
    is_premium: bool = False
    has_topics_enabled: bool = False
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
            is_premium=d.get("is_premium", False),
            has_topics_enabled=d.get("has_topics_enabled", False),
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
    is_forum: bool = False
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
            is_forum=d.get("is_forum", False),
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
    "checklist", "rich_message", "ephemeral_message",
)


@dataclass
class ChecklistTask:
    text: str
    is_completed: bool = False

    def to_dict(self):
        return {"text": self.text, "is_completed": self.is_completed}

    @classmethod
    def from_dict(cls, d):
        return cls(
            text=d.get("text", ""),
            is_completed=d.get("is_completed", False),
        )


@dataclass
class Checklist:
    title: str
    tasks: list = field(default_factory=list)

    def to_dict(self):
        return {
            "title": self.title,
            "tasks": [
                t.to_dict() if hasattr(t, "to_dict") else t
                for t in self.tasks
            ],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            title=d.get("title", ""),
            tasks=[ChecklistTask.from_dict(t) for t in d.get("tasks", [])],
        )


@dataclass
class RichMessageBlock:
    type: str
    content: dict = field(default_factory=dict)

    def to_dict(self):
        return {"type": self.type, **self.content}

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        kind = d.pop("type", "paragraph")
        return cls(type=kind, content=d)


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
    ephemeral: bool = False
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
            ephemeral=d.get("ephemeral", False),
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
class InlineQuery:
    id: str
    from_user: Optional[User] = None
    query: str = ""
    offset: str = ""
    chat_type: Optional[str] = None
    location: Optional[dict] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            from_user=User.from_dict(d["from"]) if "from" in d else None,
            query=d.get("query", ""),
            offset=d.get("offset", ""),
            chat_type=d.get("chat_type"),
            location=d.get("location"),
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
    inline_query: Optional[InlineQuery] = None
    chosen_inline_result: Optional[dict] = None
    shipping_query: Optional[dict] = None
    pre_checkout_query: Optional[dict] = None
    poll: Optional[dict] = None
    guest_message: Optional[dict] = None
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
            inline_query=(InlineQuery.from_dict(d["inline_query"])
                          if "inline_query" in d else None),
            chosen_inline_result=d.get("chosen_inline_result"),
            shipping_query=d.get("shipping_query"),
            pre_checkout_query=d.get("pre_checkout_query"),
            poll=d.get("poll"),
            guest_message=d.get("guest_message"),
            raw=d,
        )


@dataclass
class InlineQueryResultArticle:
    id: str
    title: str
    input_message_content: dict
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    reply_markup: Optional[dict] = None

    def to_dict(self):
        d = {
            "type": "article",
            "id": self.id,
            "title": self.title,
            "input_message_content": self.input_message_content,
        }
        if self.description is not None:
            d["description"] = self.description
        if self.thumbnail_url is not None:
            d["thumbnail_url"] = self.thumbnail_url
        if self.reply_markup is not None:
            d["reply_markup"] = self.reply_markup
        return d


@dataclass
class InlineQueryResultPhoto:
    id: str
    photo_url: str
    thumbnail_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    caption: Optional[str] = None
    parse_mode: Optional[str] = None
    reply_markup: Optional[dict] = None

    def to_dict(self):
        d = {
            "type": "photo",
            "id": self.id,
            "photo_url": self.photo_url,
            "thumbnail_url": self.thumbnail_url,
        }
        if self.title is not None:
            d["title"] = self.title
        if self.description is not None:
            d["description"] = self.description
        if self.caption is not None:
            d["caption"] = self.caption
        if self.parse_mode is not None:
            d["parse_mode"] = self.parse_mode
        if self.reply_markup is not None:
            d["reply_markup"] = self.reply_markup
        return d


@dataclass
class InlineQueryResultGif:
    id: str
    gif_url: str
    thumbnail_url: str
    title: Optional[str] = None
    caption: Optional[str] = None

    def to_dict(self):
        d = {
            "type": "gif",
            "id": self.id,
            "gif_url": self.gif_url,
            "thumbnail_url": self.thumbnail_url,
        }
        if self.title is not None:
            d["title"] = self.title
        if self.caption is not None:
            d["caption"] = self.caption
        return d


from .keyboards import (  # noqa: E402, F401
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
    ForceReply, RemoveKeyboard,
)
