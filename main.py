import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import config

API_TOKEN = config.token

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и хранилища состояний
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создание главной клавиатуры
buttons = ["Расписание", "Обратная связь", "Отмена записи", "Список записанных"]
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=button)] for button in buttons],
    resize_keyboard=True
)

# Создание клавиатуры для расписания
schedule_buttons = [
    "Понедельник 19:00 (Современная хор.)",
    "Среда 18:00 (Классическая хор.)",
    "Пятница 18:00 (Народная хор.)"
]
schedule_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=button)] for button in schedule_buttons],
    resize_keyboard=True
)

# Создание клавиатуры для подтверждения записи
confirmation_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)


# Состояния для машины состояний
class FeedbackState(StatesGroup):
    waiting_for_feedback = State()


class ReservationState(StatesGroup):
    waiting_for_class_selection = State()
    waiting_for_confirmation = State()
    waiting_for_fio = State()


class CancelReservationState(StatesGroup):
    waiting_for_class_selection = State()
    waiting_for_confirmation = State()
    waiting_for_fio = State()


@dp.message(Command("start"))
async def command_start(message: types.Message):
    await message.answer("Привет! Я бот для танцевальной студии. Чем я могу помочь?", reply_markup=keyboard)


@dp.message(Command("help"))
async def command_help(message: types.Message):
    help_text = (
        "Я могу помочь вам с следующими командами:\n"
        "- Расписание: посмотреть расписание занятий\n"
        "- Обратная связь: оставить обратную связь\n"
        "- Отмена записи: отменить запись на занятие\n"
        "- Список записанных: посмотреть список записанных пользователей\n"
    )
    await message.answer(help_text, reply_markup=keyboard)


@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Current state: {current_state}")
    logging.info(f"Received message: {message.text}")

    if message.text == "Расписание":
        await message.answer("Выберите одно из занятий:", reply_markup=schedule_keyboard)
        await state.set_state(ReservationState.waiting_for_class_selection)

    elif message.text == "Обратная связь":
        await message.answer("Пожалуйста, введите ваше сообщение:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(FeedbackState.waiting_for_feedback)

    elif current_state == ReservationState.waiting_for_class_selection.state and message.text in schedule_buttons:
        info_text = ""
        if message.text == "Понедельник 19:00 (Современная хор.)":
            info_text = (
                "Хореограф - Ирина Петровна. Опыт - 8 лет. Победитель международных конкурсов по современным танцам.\n\n"
                "Хотите записаться на это занятие?"
            )
        elif message.text == "Среда 18:00 (Классическая хор.)":
            info_text = (
                "Хореограф - Александр Иванович. Опыт - 10 лет. Обладатель премии за лучшие постановки в классическом танце.\n\n"
                "Хотите записаться на это занятие?"
            )
        elif message.text == "Пятница 18:00 (Народная хор.)":
            info_text = (
                "Хореограф - Ольга Сергеевна. Опыт - 6 лет. Участник национальных фестивалей народного танца.\n\n"
                "Хотите записаться на это занятие?"
            )
        await message.answer(info_text, reply_markup=confirmation_keyboard)
        await state.update_data(selected_class=message.text)
        await state.set_state(ReservationState.waiting_for_confirmation)

    elif message.text == "Да":
        if current_state == ReservationState.waiting_for_confirmation.state:
            await message.answer("Пожалуйста, введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
            await state.set_state(ReservationState.waiting_for_fio)
        elif current_state == CancelReservationState.waiting_for_confirmation.state:
            await message.answer("Пожалуйста, введите ваше ФИО для отмены записи:", reply_markup=ReplyKeyboardRemove())
            await state.set_state(CancelReservationState.waiting_for_fio)
        else:
            await message.answer("Извините, я не понимаю эту команду. Пожалуйста, выберите одну из доступных опций.",
                                 reply_markup=keyboard)

    elif message.text == "Назад":
        await message.answer("Привет! Я бот для танцевальной студии. Чем я могу помочь?", reply_markup=keyboard)
        await state.clear()

    elif current_state == ReservationState.waiting_for_fio.state:
        fio = message.text
        selected_class = (await state.get_data()).get('selected_class')

        with open("reservations.txt", "a") as file:
            file.write(f"{fio} - {selected_class}\n")

        await message.answer(f"Поздравляем, {fio}, вы записаны на занятие {selected_class}!", reply_markup=keyboard)
        await state.clear()

    elif current_state == FeedbackState.waiting_for_feedback.state:
        feedback = message.text

        with open("feedback.txt", "a") as file:
            file.write(f"{feedback}\n")

        await message.answer("Спасибо за ваше сообщение. Мы свяжемся с вами в ближайшее время.", reply_markup=keyboard)
        await state.clear()

    elif message.text == "Отмена записи":
        await message.answer("Выберите занятие для отмены записи:", reply_markup=schedule_keyboard)
        await state.set_state(CancelReservationState.waiting_for_class_selection)

    elif current_state == CancelReservationState.waiting_for_class_selection.state and message.text in schedule_buttons:
        await state.update_data(selected_class=message.text)
        await message.answer("Хотите отменить запись на это занятие?", reply_markup=confirmation_keyboard)
        await state.set_state(CancelReservationState.waiting_for_confirmation)

    elif current_state == CancelReservationState.waiting_for_fio.state:
        fio = message.text
        selected_class = (await state.get_data()).get('selected_class')
        updated_lines = []

        with open("reservations.txt", "r") as file:
            lines = file.readlines()

        with open("reservations.txt", "w") as file:
            for line in lines:
                if not line.strip() == f"{fio} - {selected_class}":
                    updated_lines.append(line)
            file.writelines(updated_lines)

        await message.answer(f"Запись на занятие {selected_class} для {fio} отменена.", reply_markup=keyboard)
        await state.clear()

    elif message.text == "Список записанных":
        records = []
        with open("reservations.txt", "r") as file:
            records = file.readlines()

        if records:
            response = "Список записанных пользователей:\n" + "".join(records)
        else:
            response = "Нет записанных пользователей."

        await message.answer(response, reply_markup=keyboard)

    else:
        await message.answer("Извините, я не понимаю эту команду. Пожалуйста, выберите одну из доступных опций.",
                             reply_markup=keyboard)


async def main():
    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
