from puragram import escape_html, escape_markdown, split_message


def test_escape_html():
    assert escape_html("<b>&</b>") == "&lt;b&gt;&amp;&lt;/b&gt;"


def test_escape_markdown():
    assert escape_markdown("a.b") == r"a\.b"


def test_split_short():
    assert split_message("hello", limit=10) == ["hello"]


def test_split_long():
    text = "aaa\n" * 10
    chunks = split_message(text, limit=10)
    assert all(len(c) <= 10 for c in chunks)