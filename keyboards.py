from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def user_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Частые вопросы"), KeyboardButton(text="Задать вопрос")]],
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Добавить вопрос"),
                KeyboardButton(text="Список вопросов"),
            ],
            [KeyboardButton(text="Удалить вопрос"), KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def build_faq_keyboard(faqs: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for faq_id, question in faqs:
        builder.row(
            InlineKeyboardButton(
                text=question,
                callback_data=f"faq:{faq_id}",
            )
        )
    return builder.as_markup()


def build_admin_reply_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Ответить пользователю",
            callback_data=f"reply:{user_id}",
        )
    )
    return builder.as_markup()
