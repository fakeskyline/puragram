import os

import pytest

import zeed.security as sec
from zeed import (
    MAX_CALLBACK_DATA,
    MAX_CAPTION_LEN,
    MAX_MESSAGE_LEN,
    MAX_REGEX_LEN,
    MAX_UPLOAD_BYTES,
    MAX_WEBHOOK_BYTES,
    check_size,
    compile_safe_regex,
    constant_time_eq,
    mask_token,
    redact,
    safe_filename,
    safe_path,
    validate_callback_data,
    validate_text,
)


def test_redact_simple_token():
    s = "error: 1234567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    out = redact(s)
    assert "AAHxxxx" not in out
    assert "***REDACTED***" in out
    assert "1234567890" in out


def test_redact_short_token_untouched():
    s = "not a token: 123:abc"
    assert redact(s) == s


def test_redact_multiple_tokens():
    s = ("bad 1111111111:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA "
         "and 2222222222:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
    out = redact(s)
    assert out.count("***REDACTED***") == 2


def test_redact_none_and_empty():
    assert redact(None) is None
    assert redact("") == ""


def test_redact_non_string():
    assert redact(12345) == "12345"


def test_mask_token_normal():
    token = "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert mask_token(token) == "12345678…WXYZ"


def test_mask_token_short():
    assert mask_token("short") == "***"
    assert mask_token("") == "***"
    assert mask_token(None) == "***"


def test_mask_token_does_not_leak_middle():
    token = "1234567890:VERYSECRETMIDDLEPART1234567890XYZ"
    masked = mask_token(token)
    assert "SECRET" not in masked
    assert "MIDDLE" not in masked


def test_callback_data_ok():
    assert validate_callback_data("hi") == "hi"
    assert validate_callback_data("a" * 64) == "a" * 64


def test_callback_data_none():
    assert validate_callback_data(None) is None


def test_callback_data_too_long_ascii():
    with pytest.raises(ValueError):
        validate_callback_data("x" * 65)


def test_callback_data_too_long_utf8():
    with pytest.raises(ValueError):
        validate_callback_data("x" * 65)


def test_callback_data_null_byte():
    with pytest.raises(ValueError):
        validate_callback_data("hi\x00there")


def test_callback_data_wrong_type():
    with pytest.raises(ValueError):
        validate_callback_data(123)


def test_validate_text_ok():
    assert validate_text("hello") == "hello"


def test_validate_text_none():
    assert validate_text(None) is None


def test_validate_text_too_long():
    with pytest.raises(ValueError):
        validate_text("x" * (MAX_MESSAGE_LEN + 1))


def test_validate_text_custom_limit():
    with pytest.raises(ValueError):
        validate_text("x" * 11, limit=10)


def test_validate_text_converts_to_str():
    assert validate_text(12345) == "12345"


def test_safe_path_normal_file(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hi")
    result = safe_path(str(f))
    assert os.path.isfile(result)


def test_safe_path_must_exist_false(tmp_path):
    target = tmp_path / "nonexistent.txt"
    result = safe_path(str(target), must_exist=False)
    assert result.endswith("nonexistent.txt")


def test_safe_path_not_found():
    with pytest.raises(ValueError):
        safe_path("/tmp/this-file-does-not-exist-12345.txt")


def test_safe_path_wrong_type():
    with pytest.raises(ValueError):
        safe_path(12345)


def test_safe_path_forbidden_etc(monkeypatch):
    monkeypatch.setattr(sec.os.path, "realpath", lambda p: "/etc/passwd")
    with pytest.raises(ValueError):
        sec.safe_path("/etc/passwd")


def test_safe_path_forbidden_proc(monkeypatch):
    monkeypatch.setattr(sec.os.path, "realpath", lambda p: "/proc/self/environ")
    with pytest.raises(ValueError):
        sec.safe_path("/proc/self/environ")


def test_safe_path_forbidden_sys(monkeypatch):
    monkeypatch.setattr(sec.os.path, "realpath", lambda p: "/sys/kernel")
    with pytest.raises(ValueError):
        sec.safe_path("/sys/kernel")


def test_safe_path_forbidden_root(monkeypatch):
    monkeypatch.setattr(sec.os.path, "realpath", lambda p: "/root/.ssh/id_rsa")
    with pytest.raises(ValueError):
        sec.safe_path("/root/.ssh/id_rsa")


def test_safe_path_forbidden_dev(monkeypatch):
    monkeypatch.setattr(sec.os.path, "realpath", lambda p: "/dev/urandom")
    with pytest.raises(ValueError):
        sec.safe_path("/dev/urandom")


def test_safe_path_escape_base_dir(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("x")
    with pytest.raises(ValueError):
        safe_path(str(outside), base_dir=str(base))


def test_safe_path_inside_base_dir(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    inside = base / "file.txt"
    inside.write_text("ok")
    result = safe_path(str(inside), base_dir=str(base))
    assert os.path.isfile(result)


def test_safe_path_dotdot_escape(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("x")
    sneaky = str(base / ".." / "secret.txt")
    with pytest.raises(ValueError):
        safe_path(sneaky, base_dir=str(base))


def test_check_size_ok(tmp_path):
    f = tmp_path / "small.bin"
    f.write_bytes(b"x" * 100)
    assert check_size(str(f)) == 100


def test_check_size_too_large(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 200)
    with pytest.raises(ValueError):
        check_size(str(f), max_bytes=100)


def test_check_size_zero(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    assert check_size(str(f)) == 0


def test_safe_filename_basename():
    assert safe_filename("/etc/passwd") == "passwd"
    assert safe_filename("../../secret.txt") == "secret.txt"


def test_safe_filename_control_chars():
    assert "\x00" not in safe_filename("bad\x00name.txt")
    assert "\n" not in safe_filename("bad\nname.txt")


def test_safe_filename_slashes():
    assert "/" not in safe_filename("a/b/c.txt")
    assert "\\" not in safe_filename("a\\b\\c.txt")


def test_safe_filename_empty():
    assert safe_filename("") == "file.bin"
    assert safe_filename(None) == "file.bin"


def test_safe_filename_too_long():
    long_name = "a" * 500 + ".txt"
    result = safe_filename(long_name)
    assert len(result) <= 255


def test_safe_filename_unicode_nfkc():
    weird = "file.txt"
    result = safe_filename(weird)
    assert "file" in result or "fi" in result


def test_constant_time_eq_match():
    assert constant_time_eq("abc", "abc") is True


def test_constant_time_eq_mismatch():
    assert constant_time_eq("abc", "abd") is False


def test_constant_time_eq_none():
    assert constant_time_eq(None, "abc") is False
    assert constant_time_eq("abc", None) is False
    assert constant_time_eq(None, None) is False


def test_constant_time_eq_different_length():
    assert constant_time_eq("a", "aaaaaaaaaa") is False


def test_constant_time_eq_empty():
    assert constant_time_eq("", "") is True


def test_safe_regex_simple():
    r = compile_safe_regex(r"^\d+$")
    assert r.search("123")
    assert not r.search("abc")


def test_safe_regex_passthrough():
    import re
    compiled = re.compile(r"hello")
    assert compile_safe_regex(compiled) is compiled


def test_safe_regex_too_long():
    with pytest.raises(ValueError):
        compile_safe_regex("a" * (MAX_REGEX_LEN + 1))


def test_safe_regex_dos_nested_plus():
    with pytest.raises(ValueError):
        compile_safe_regex("(a+)+$")


def test_safe_regex_dos_nested_star():
    with pytest.raises(ValueError):
        compile_safe_regex("(a*)*$")


def test_safe_regex_dos_alternation():
    with pytest.raises(ValueError):
        compile_safe_regex("(a|a)+$")


def test_safe_regex_ok_quantifier_groups():
    r = compile_safe_regex(r"^(ab)+$")
    assert r.search("abab")


def test_limits_values():
    assert MAX_MESSAGE_LEN == 4096
    assert MAX_CAPTION_LEN == 1024
    assert MAX_CALLBACK_DATA == 64
    assert MAX_UPLOAD_BYTES == 50 * 1024 * 1024
    assert MAX_WEBHOOK_BYTES == 1 * 1024 * 1024
    assert MAX_REGEX_LEN == 500