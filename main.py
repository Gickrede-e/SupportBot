import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS, BOT_TOKEN, DB_PATH
from db import FaqStorage
from keyboards import (
    admin_menu,
    build_admin_reply_keyboard,
    build_faq_keyboard,
    user_menu,
)
from states import AddFaq, AdminReply, AskAdmin, DeleteFaq

router = Router()
storage = FaqStorage(DB_PATH)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def send_admin_request(message: Message, question: str) -> bool:
    if not ADMIN_IDS:
        await message.answer(
            "Администраторы еще не настроены. Попробуйте позже."
        )
        return False
    if not message.from_user:
        await message.answer("Не удалось определить ваш аккаунт.")
        return False
    user = message.from_user
    text = (
        "Новый вопрос пользователя:\n"
        f"От: {user.full_name} (ID: {user.id})\n"
        f"Вопрос: {question}"
    )
    for admin_id in ADMIN_IDS:
        await message.bot.send_message(
            admin_id,
            text,
            reply_markup=build_admin_reply_keyboard(user.id),
        )
    return True


async def send_faq_list(message: Message) -> None:
    faqs = await storage.list()
    if not faqs:
        await message.answer("Пока нет частых вопросов. Попробуйте позже.")
        return
    await message.answer("Выберите вопрос:", reply_markup=build_faq_keyboard(faqs))


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Здравствуйте! Я бот поддержки. Откройте меню с частыми вопросами."
    )
    await message.answer(text, reply_markup=user_menu())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "Команды:\n"
        "/faq - частые вопросы\n"
        "/ask - задать вопрос администратору\n"
        "/admin - панель администратора (только для админов)"
    )
    await message.answer(text, reply_markup=user_menu())


@router.message(Command("faq"))
async def cmd_faq(message: Message) -> None:
    await send_faq_list(message)


@router.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext) -> None:
    await state.set_state(AskAdmin.question)
    await message.answer("Напишите ваш вопрос администратору:")


@router.message(F.text.in_(["Частые вопросы", "частые вопросы"]))
async def menu_faq(message: Message) -> None:
    await send_faq_list(message)


@router.message(F.text.in_(["Задать вопрос", "задать вопрос"]))
async def menu_ask_admin(message: Message, state: FSMContext) -> None:
    await state.set_state(AskAdmin.question)
    await message.answer("Напишите ваш вопрос администратору:")


@router.callback_query(F.data.startswith("faq:"))
async def faq_callback(query: CallbackQuery) -> None:
    await query.answer()
    raw_id = query.data.split(":", 1)[1]
    if not raw_id.isdigit():
        await query.message.answer("Извините, этот вопрос некорректен.")
        return
    faq_id = int(raw_id)
    faq = await storage.get(faq_id)
    if faq is None:
        await query.message.answer("Этот вопрос больше не существует.")
        return
    _, question, answer = faq
    await query.message.answer(f"Вопрос: {question}\n\nОтвет: {answer}")


@router.callback_query(F.data.startswith("reply:"))
async def reply_callback(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if not query.from_user or not is_admin(query.from_user.id):
        await query.message.answer("У вас нет доступа для ответа.")
        return
    raw_id = query.data.split(":", 1)[1]
    if not raw_id.isdigit():
        await query.message.answer("Некорректный ID пользователя.")
        return
    await state.set_state(AdminReply.answer)
    await state.update_data(user_id=int(raw_id))
    await query.message.answer(
        f"Отправьте ответ пользователю {raw_id}:"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к панели администратора.")
        return
    await message.answer("Панель администратора:", reply_markup=admin_menu())


@router.message(Command("add_faq"))
async def cmd_add_faq(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к добавлению вопросов.")
        return
    await state.set_state(AddFaq.question)
    await message.answer("Отправьте текст вопроса:")


@router.message(Command("list_faqs"))
async def cmd_list_faqs(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к списку вопросов.")
        return
    faqs = await storage.list()
    if not faqs:
        await message.answer("Пока нет вопросов.")
        return
    lines = [f"{faq_id}. {question}" for faq_id, question in faqs]
    await message.answer("Вопросы:\n" + "\n".join(lines), reply_markup=admin_menu())


@router.message(Command("delete_faq"))
async def cmd_delete_faq(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к удалению вопросов.")
        return
    await state.set_state(DeleteFaq.faq_id)
    await message.answer("Отправьте ID вопроса для удаления:")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=user_menu())


@router.message(F.text == "Добавить вопрос")
async def admin_add_faq(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddFaq.question)
    await message.answer("Отправьте текст вопроса:")


@router.message(F.text == "Список вопросов")
async def admin_list_faqs(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    faqs = await storage.list()
    if not faqs:
        await message.answer("Пока нет вопросов.")
        return
    lines = [f"{faq_id}. {question}" for faq_id, question in faqs]
    await message.answer("Вопросы:\n" + "\n".join(lines), reply_markup=admin_menu())


@router.message(F.text == "Удалить вопрос")
async def admin_delete_faq(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.set_state(DeleteFaq.faq_id)
    await message.answer("Отправьте ID вопроса для удаления:")


@router.message(F.text == "Назад")
async def admin_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Возврат в главное меню.", reply_markup=user_menu())


@router.message(AddFaq.question)
async def add_faq_question(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    question = (message.text or "").strip()
    if not question:
        await message.answer("Вопрос не может быть пустым. Отправьте снова:")
        return
    await state.update_data(question=question)
    await state.set_state(AddFaq.answer)
    await message.answer("Отправьте текст ответа:")


@router.message(AddFaq.answer)
async def add_faq_answer(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("Ответ не может быть пустым. Отправьте снова:")
        return
    data = await state.get_data()
    question = data.get("question", "")
    faq_id = await storage.add(question, answer)
    await state.clear()
    await message.answer(
        f"Вопрос добавлен с ID {faq_id}.",
        reply_markup=admin_menu(),
    )


@router.message(DeleteFaq.faq_id)
async def delete_faq_id(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    raw_id = (message.text or "").strip()
    if not raw_id.isdigit():
        await message.answer("Пожалуйста, отправьте числовой ID вопроса:")
        return
    faq_id = int(raw_id)
    deleted = await storage.delete(faq_id)
    await state.clear()
    if deleted:
        await message.answer(
            f"Вопрос {faq_id} удален.",
            reply_markup=admin_menu(),
        )
    else:
        await message.answer(
            f"Вопрос {faq_id} не найден.",
            reply_markup=admin_menu(),
        )


@router.message(AskAdmin.question)
async def ask_admin_question(message: Message, state: FSMContext) -> None:
    question = (message.text or "").strip()
    if not question:
        await message.answer("Вопрос не может быть пустым. Отправьте снова:")
        return
    await state.clear()
    sent = await send_admin_request(message, question)
    if sent:
        await message.answer(
            "Спасибо! Администратор скоро ответит здесь.",
            reply_markup=user_menu(),
        )


@router.message(AdminReply.answer)
async def admin_reply_answer(message: Message, state: FSMContext) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await state.clear()
        return
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("Ответ не может быть пустым. Отправьте снова:")
        return
    data = await state.get_data()
    user_id = data.get("user_id")
    await state.clear()
    if not isinstance(user_id, int):
        await message.answer(
            "Не найден ID пользователя. Повторите из панели администратора.",
            reply_markup=admin_menu(),
        )
        return
    try:
        await message.bot.send_message(
            user_id,
            f"Ответ поддержки:\n{answer}",
        )
        await message.answer(
            f"Ответ отправлен пользователю {user_id}.",
            reply_markup=admin_menu(),
        )
    except Exception:
        await message.answer(
            f"Не удалось отправить ответ пользователю {user_id}.",
            reply_markup=admin_menu(),
        )


async def on_startup() -> None:
    await storage.init()


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")

    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.startup.register(on_startup)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
