import re
from typing import TypeVar

from .security import MAX_MESSAGE_LEN

T = TypeVar("T")

_MD_V2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def escape_html(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def escape_markdown(text):
    out = []
    for ch in str(text):
        if ch in _MD_V2_SPECIAL:
            out.append("\\")
        out.append(ch)
    return "".join(out)


def safe_text(text, parse_mode="HTML"):
    if text is None:
        return None
    if parse_mode == "HTML":
        return escape_html(text)
    if parse_mode in ("MarkdownV2", "Markdown"):
        return escape_markdown(text)
    return str(text)


def split_message(text, limit=MAX_MESSAGE_LEN, prefer="\n"):
    text = str(text)
    if len(text) <= limit:
        return [text]
    chunks, rest = [], text
    while len(rest) > limit:
        cut = rest.rfind(prefer, 0, limit)
        if cut == -1:
            cut = rest.rfind(" ", 0, limit)
        if cut == -1:
            cut = limit
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        chunks.append(rest)
    return chunks


def chunked(iterable, size):
    buf = []
    for item in iterable:
        buf.append(item)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf


def user_mention(user, html=True):
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    if user.username and not html:
        return f"@{user.username}"
    if html:
        return f'<a href="tg://user?id={int(user.id)}">{escape_html(name)}</a>'
    return name


def truncate(text, limit, suffix="…"):
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:max(0, limit - len(suffix))] + suffix