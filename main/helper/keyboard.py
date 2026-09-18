"""
Helper functions ikb (inline keyboard) and kb (reply keyboard)
originally from navycodes/pyrogram fork, ported here for compatibility.
"""
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def ikb(rows=None):
    """
    Build an InlineKeyboardMarkup from a nested list.
    Each inner list is a row of buttons.
    Each button is a tuple: (text, value) or (text, value, type)
      - type defaults to 'callback_data'
    Example:
        ikb([[("Button", "data")], [("URL", "https://...", "url")]])
    """
    if rows is None:
        rows = []
    lines = []
    for row in rows:
        line = []
        for button in row:
            text = button[0]
            value = button[1]
            btn_type = button[2] if len(button) > 2 else "callback_data"
            line.append(InlineKeyboardButton(text, **{btn_type: value}))
        lines.append(line)
    return InlineKeyboardMarkup(lines)


def kb(rows=None, **kwargs):
    """
    Build a ReplyKeyboardMarkup from a nested list.
    Each inner list is a row of buttons.
    Each button is a string or tuple: (text,) or (text, request_contact, request_location)
    Example:
        kb([["Button 1", "Button 2"], ["Button 3"]])
    """
    if rows is None:
        rows = []
    lines = []
    for row in rows:
        line = []
        for button in row:
            if isinstance(button, str):
                line.append(KeyboardButton(button))
            elif isinstance(button, (list, tuple)):
                text = button[0]
                request_contact = button[1] if len(button) > 1 else False
                request_location = button[2] if len(button) > 2 else False
                line.append(
                    KeyboardButton(
                        text,
                        request_contact=request_contact,
                        request_location=request_location,
                    )
                )
            else:
                line.append(KeyboardButton(str(button)))
        lines.append(line)
    return ReplyKeyboardMarkup(lines, **kwargs)
