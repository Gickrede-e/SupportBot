from aiogram.fsm.state import State, StatesGroup


class AddFaq(StatesGroup):
    question = State()
    answer = State()


class DeleteFaq(StatesGroup):
    faq_id = State()


class AskAdmin(StatesGroup):
    question = State()


class AdminReply(StatesGroup):
    answer = State()
