"""Demo of zeed 1.3.0 features: colored buttons, checklists, drafts,
ephemeral messages, rich messages.

Run: python examples/telegram_features.py
"""
import logging
import time

from zeed import (
    Bot,
    Checklist,
    ChecklistTask,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    RichMessageBlock,
    setup_logging,
)

setup_logging(level=logging.INFO)

TOKEN = "YOUR_TOKEN_HERE"
bot = Bot(TOKEN, parse_mode="HTML")


@bot.message_handler(commands=["start"])
def start(msg):
    kb = InlineKeyboardMarkup().row(
        InlineKeyboardButton("Primary", callback_data="a", style="primary"),
        InlineKeyboardButton("Danger", callback_data="b", style="danger"),
    ).row(
        InlineKeyboardButton("Success", callback_data="c", style="success"),
        InlineKeyboardButton("Star ⭐", callback_data="d",
                             icon_custom_emoji_id="5368324170671202286"),
    )
    bot.send_message(
        msg.chat.id,
        "Demo of <b>Bot API 9.4</b> colored buttons:",
        reply_markup=kb,
    )


@bot.message_handler(commands=["checklist"])
def checklist_demo(msg):
    cl = Checklist("Shopping list", [
        ChecklistTask("Bread", is_completed=True),
        ChecklistTask("Eggs"),
        ChecklistTask("Milk"),
    ])
    bot.send_checklist(msg.chat.id, cl)


@bot.message_handler(commands=["rich"])
def rich_demo(msg):
    blocks = [
        RichMessageBlock(type="heading", content={"text": "Rich message"}),
        RichMessageBlock(type="paragraph",
                         content={"text": "This is block-based content."}),
        RichMessageBlock(type="list", content={
            "items": ["One", "Two", "Three"],
        }),
    ]
    bot.send_rich_message(msg.chat.id, blocks)


@bot.message_handler(commands=["draft"])
def draft_demo(msg):
    """Simulates ChatGPT-style streaming using sendMessageDraft."""
    draft_id = int(time.time())
    full_text = "Thinking... generating a long answer..."
    for i in range(1, len(full_text) + 1, 5):
        bot.send_message_draft(msg.chat.id, draft_id, full_text[:i])
        time.sleep(0.15)
    bot.send_message(msg.chat.id, full_text)


@bot.message_handler(commands=["ephemeral"])
def ephemeral_demo(msg):
    if msg.from_user is None:
        return
    bot.send_ephemeral_message(
        msg.chat.id,
        "Only you can see this message. It disappears after reading.",
        receiver_user_id=msg.from_user.id,
    )


@bot.message_handler(commands=["managed"])
def managed_demo(msg):
    """Get a token for a managed bot (if you have one)."""
    bot_id = 1234567890  # replace with your managed bot id
    try:
        result = bot.get_managed_bot_token(bot_id)
        bot.send_message(msg.chat.id, f"Managed bot token: {result[:10]}...")
    except Exception as e:
        bot.send_message(msg.chat.id, f"Not a managed bot owner: {e}")


if __name__ == "__main__":
    print("Demo bot. Commands: /start /checklist /rich /draft /ephemeral /managed")
    bot.run_polling()
