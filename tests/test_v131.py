"""Tests for zeed 1.3.1 validation fixes."""
import pytest

from zeed import Bot
from zeed.exceptions import ValidationError


@pytest.fixture
def bot():
    return Bot("1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", retries=0)


# ─── send_message_draft ───

def test_draft_rejects_group_chat(bot):
    with pytest.raises(ValidationError) as e:
        bot.send_message_draft(-100123456, 1, "hello")
    assert "private" in str(e.value).lower()


def test_draft_rejects_zero_id(bot):
    with pytest.raises(ValidationError) as e:
        bot.send_message_draft(123456, 0, "hello")
    assert "non-zero" in str(e.value).lower()


def test_draft_accepts_positive_id_and_draft_id(bot):
    # Should not raise before hitting the network
    try:
        bot.send_message_draft(123456, 1, "hello")
    except ValidationError:
        pytest.fail("Should not raise ValidationError for valid inputs")
    except Exception:
        # network / api error — expected, since token is fake
        pass


# ─── send_ephemeral_message ───

def test_ephemeral_rejects_private_chat(bot):
    with pytest.raises(ValidationError) as e:
        bot.send_ephemeral_message(123456, "hi", receiver_user_id=1)
    assert "group" in str(e.value).lower()


def test_ephemeral_requires_receiver_or_callback(bot):
    with pytest.raises(ValidationError) as e:
        bot.send_ephemeral_message(-100123456, "hi")
    assert "receiver_user_id" in str(e.value).lower()


def test_ephemeral_accepts_group_chat(bot):
    try:
        bot.send_ephemeral_message(-100123456, "hi", receiver_user_id=1)
    except ValidationError:
        pytest.fail("Should not raise ValidationError for valid inputs")
    except Exception:
        pass


def test_ephemeral_accepts_callback_id(bot):
    try:
        bot.send_ephemeral_message(-100123456, "hi", callback_query_id="abc")
    except ValidationError:
        pytest.fail("Should not raise ValidationError for valid inputs")
    except Exception:
        pass
