import os
import re
import hmac
import unicodedata

MAX_MESSAGE_LEN = 4096
MAX_CAPTION_LEN = 1024
MAX_CALLBACK_DATA = 64
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_WEBHOOK_BYTES = 1 * 1024 * 1024
MAX_REGEX_LEN = 500

_TOKEN_RE = re.compile(r"\b(\d{6,12}):([A-Za-z0-9_\-]{20,})\b")
_FORBIDDEN_PREFIXES = ("/etc", "/proc", "/sys", "/root", "/dev")
_UNSAFE_NAME = re.compile(r"[\x00-\x1f/\\]")
_NESTED_QUANTIFIERS = re.compile(r"\([^)]*[+*][^)]*\)[+*]")
_ALTERNATION_QUANTIFIED = re.compile(r"\([^)]*\|[^)]*\)\s*[+*{]")


def redact(text):
    if not text:
        return text
    return _TOKEN_RE.sub(r"\1:***REDACTED***", str(text))


def mask_token(token):
    if not token or len(token) < 16:
        return "***"
    return f"{token[:8]}…{token[-4:]}"


def safe_path(path, base_dir=None, must_exist=True):
    if not isinstance(path, str):
        raise ValueError("path must be a string")

    p = os.path.realpath(os.path.abspath(path))

    if any(p == f or p.startswith(f + os.sep) for f in _FORBIDDEN_PREFIXES):
        raise ValueError(f"Access to {p} is forbidden")

    if base_dir is not None:
        base = os.path.realpath(os.path.abspath(base_dir))
        if not (p == base or p.startswith(base + os.sep)):
            raise ValueError(f"Path escapes base_dir: {p}")

    if must_exist and not os.path.isfile(p):
        raise ValueError(f"File not found: {p}")

    return p


def check_size(path, max_bytes=MAX_UPLOAD_BYTES):
    size = os.path.getsize(path)
    if size > max_bytes:
        raise ValueError(
            f"File too large: {size} > {max_bytes} bytes "
            f"({size / 1024 / 1024:.1f} MB)"
        )
    return size


def validate_callback_data(data):
    if data is None:
        return None
    if not isinstance(data, str):
        raise ValueError("callback_data must be str")
    encoded = data.encode("utf-8")
    if len(encoded) > MAX_CALLBACK_DATA:
        raise ValueError(
            f"callback_data too long: {len(encoded)} bytes "
            f"(max {MAX_CALLBACK_DATA})"
        )
    if "\x00" in data:
        raise ValueError("callback_data contains NUL byte")
    return data


def validate_text(text, limit=MAX_MESSAGE_LEN):
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)
    if len(text) > limit:
        raise ValueError(f"Text too long: {len(text)} > {limit}")
    return text


def constant_time_eq(a, b):
    if a is None or b is None:
        return False
    if isinstance(a, str):
        a = a.encode()
    if isinstance(b, str):
        b = b.encode()
    return hmac.compare_digest(a, b)


def safe_filename(name, fallback="file.bin"):
    if not name:
        return fallback
    name = os.path.basename(str(name))
    name = _UNSAFE_NAME.sub("_", name)
    name = unicodedata.normalize("NFKC", name)
    name = name[:255]
    return name or fallback


def compile_safe_regex(pattern, flags=0):
    if isinstance(pattern, str):
        if len(pattern) > MAX_REGEX_LEN:
            raise ValueError(f"Regex too long: {len(pattern)}")

        if _NESTED_QUANTIFIERS.search(pattern):
            raise ValueError(
                "Potentially catastrophic regex (nested quantifiers)"
            )

        if _ALTERNATION_QUANTIFIED.search(pattern):
            raise ValueError(
                "Potentially catastrophic regex "
                "(alternation inside quantified group)"
            )

        return re.compile(pattern, flags)

    return pattern


__all__ = [
    "redact", "mask_token",
    "safe_path", "check_size", "safe_filename",
    "validate_callback_data", "validate_text",
    "constant_time_eq", "compile_safe_regex",
    "MAX_MESSAGE_LEN", "MAX_CAPTION_LEN", "MAX_CALLBACK_DATA",
    "MAX_UPLOAD_BYTES", "MAX_WEBHOOK_BYTES", "MAX_REGEX_LEN",
]