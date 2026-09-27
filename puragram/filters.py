from .security import compile_safe_regex


class BaseFilter:
    def __call__(self, event):
        raise NotImplementedError

    def __and__(self, other):
        return _And(self, _ensure(other))

    def __or__(self, other):
        return _Or(self, _ensure(other))

    def __invert__(self):
        return _Not(self)


def _ensure(f):
    if isinstance(f, BaseFilter):
        return f
    if callable(f):
        return Func(f)
    raise TypeError(f"Not a filter: {f!r}")


class _And(BaseFilter):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def __call__(self, e):
        return self.a(e) and self.b(e)


class _Or(BaseFilter):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def __call__(self, e):
        return self.a(e) or self.b(e)


class _Not(BaseFilter):
    def __init__(self, a):
        self.a = a

    def __call__(self, e):
        return not self.a(e)


class Func(BaseFilter):
    def __init__(self, func):
        self.func = func

    def __call__(self, e):
        return bool(self.func(e))


class Command(BaseFilter):
    def __init__(self, *cmds, prefix="/"):
        if not cmds:
            raise ValueError("At least one command required")
        self.cmds = {c.lstrip(prefix).lower() for c in cmds}
        self.prefix = prefix

    def __call__(self, msg):
        text = getattr(msg, "text", None) or ""
        if not text.startswith(self.prefix):
            return False
        head = text[len(self.prefix):].split(maxsplit=1)[0]
        cmd = head.split("@", 1)[0].lower()
        return cmd in self.cmds


class Text(BaseFilter):
    def __init__(self, *variants, ignore_case=True):
        if not variants:
            raise ValueError("At least one variant required")
        self.ignore_case = ignore_case
        if ignore_case:
            self.variants = {str(v).lower() for v in variants}
        else:
            self.variants = set(variants)

    def __call__(self, msg):
        text = getattr(msg, "text", None)
        if text is None:
            return False
        return (text.lower() if self.ignore_case else text) in self.variants


class ContentTypes(BaseFilter):
    def __init__(self, *types):
        self.types = set(types)

    def __call__(self, msg):
        return getattr(msg, "content_type", None) in self.types


class ChatType(BaseFilter):
    def __init__(self, *types):
        self.types = set(types)

    def __call__(self, obj):
        chat = getattr(obj, "chat", None)
        return bool(chat and chat.type in self.types)


class ChatId(BaseFilter):
    def __init__(self, *ids):
        self.ids = set(int(i) for i in ids)

    def __call__(self, obj):
        chat = getattr(obj, "chat", None)
        return bool(chat and chat.id in self.ids)


class UserId(BaseFilter):
    def __init__(self, *ids):
        self.ids = set(int(i) for i in ids)

    def __call__(self, obj):
        u = getattr(obj, "from_user", None)
        return bool(u and u.id in self.ids)


class Regexp(BaseFilter):
    def __init__(self, pattern, flags=0):
        self.re = compile_safe_regex(pattern, flags)

    def __call__(self, msg):
        text = (getattr(msg, "text", None)
                or getattr(msg, "caption", None) or "")
        return bool(self.re.search(text))


class CallbackData(BaseFilter):
    def __init__(self, *variants):
        self.variants = set(variants)

    def __call__(self, obj):
        return getattr(obj, "data", None) in self.variants


def build_named(**named):
    parts = []
    if "commands" in named:
        parts.append(Command(*named.pop("commands")))
    if "content_types" in named:
        parts.append(ContentTypes(*named.pop("content_types")))
    if "chat_types" in named:
        parts.append(ChatType(*named.pop("chat_types")))
    if "chat_id" in named:
        v = named.pop("chat_id")
        parts.append(ChatId(*(v if isinstance(v, (list, tuple, set)) else [v])))
    if "user_id" in named:
        v = named.pop("user_id")
        parts.append(UserId(*(v if isinstance(v, (list, tuple, set)) else [v])))
    if "text" in named:
        v = named.pop("text")
        parts.append(Text(*(v if isinstance(v, (list, tuple, set)) else [v])))
    if "callback_data" in named:
        v = named.pop("callback_data")
        parts.append(CallbackData(*(v if isinstance(v, (list, tuple, set)) else [v])))
    if "regexp" in named:
        parts.append(Regexp(named.pop("regexp")))
    if "func" in named:
        parts.append(Func(named.pop("func")))

    if named:
        raise TypeError(f"Unknown filter kwargs: {list(named)}")

    if not parts:
        return None
    out = parts[0]
    for p in parts[1:]:
        out = out & p
    return out