import asyncio
import logging
import os
import json
import aiohttp
import re

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, Command
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
API_BASE_URL = "https://platform-api.max.ru"
SETTINGS_FILE = "settings.json"

bot = Bot(TOKEN)
dp = Dispatcher()

# Хранилище настроек для каждого пользователя
user_settings = {}


def load_settings():
    global user_settings
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        # JSON keys are strings, convert back to int
        user_settings = {int(k): v for k, v in data.items()}
        logging.info(f"⚙️ Загружены настройки для {len(user_settings)} пользователей")


def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(user_settings, f)


async def add_button_to_message(message_id: str, discussion_url: str):
    keyboard = {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {
                        "type": "link",
                        "text": "Прокомментировать",
                        "url": discussion_url
                    }
                ]
            ]
        }
    }

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        url_api = f"{API_BASE_URL}/messages?message_id={message_id}"

        async with session.put(url_api, headers=headers, json={"attachments": [keyboard]}) as resp:
            if resp.status == 200:
                logging.info(f"✅ Кнопка добавлена к {message_id}")
                return True
            else:
                error = await resp.text()
                logging.error(f"❌ Ошибка edit_message: {resp.status} - {error}")
                return False


# ВАЖНО: on_channel_post должен быть зарегистрирован ДО handle_text,
# иначе handle_text перехватит событие первым и on_channel_post не вызовется.
@dp.message_created()
async def on_channel_post(event: MessageCreated):
    chat_type = event.message.recipient.chat_type
    if chat_type != ChatType.CHANNEL:
        return

    message_id = event.message.body.mid if event.message.body else None
    logging.info(f"📢 Пост в канале: message_id={message_id}")

    if not message_id:
        logging.warning("⚠️ message_id не найден (body=None)")
        return

    discussion_url = None
    for settings in user_settings.values():
        if settings.get("discussion_url"):
            discussion_url = settings["discussion_url"]
            break

    if not discussion_url:
        logging.warning("⚠️ Нет сохранённой ссылки на обсуждение. Запусти /start и настрой бота.")
        return

    await add_button_to_message(message_id, discussion_url)


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return

    user_id = event.message.sender.user_id

    if user_id not in user_settings:
        user_settings[user_id] = {}

    user_settings[user_id]["waiting_for"] = "channel_url"
    save_settings()

    text = (
        "👋 Привет! Я бот Комментарии для канала.\n\n"
        "Давай настроим твоего бота.\n\n"
        "**Шаг 1 из 2:**\n"
        "Отправь мне **ссылку на твой канал**.\n\n"
        "Ссылка выглядит так: `https://max.ru/c/XXXXXXXX`"
    )
    await event.message.answer(text)


@dp.message_created()
async def handle_text(event: MessageCreated):
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return

    user_id = event.message.sender.user_id
    text = event.message.body.text if event.message.body else ""

    if user_id not in user_settings:
        await event.message.answer("Напиши /start, чтобы начать настройку")
        return

    waiting_for = user_settings[user_id].get("waiting_for")

    url_match = re.search(r'https://max\.ru/(?:c|join)/[\w-]+', text)
    if not url_match:
        await event.message.answer("❌ Не нашёл ссылку")
        return

    url = url_match.group(0)

    if waiting_for == "channel_url":
        user_settings[user_id]["channel_url"] = url
        user_settings[user_id]["waiting_for"] = "discussion_url"
        save_settings()
        await event.message.answer(
            f"✅ Ссылка на канал сохранена\n\n"
            f"**Шаг 2 из 2:**\n"
            f"Отправь мне **ссылку на чат для обсуждений**"
        )

    elif waiting_for == "discussion_url":
        if '/join/' not in url:
            await event.message.answer("❌ Это не ссылка на чат обсуждений")
            return

        user_settings[user_id]["discussion_url"] = url
        user_settings[user_id]["waiting_for"] = None
        save_settings()

        await event.message.answer(
            f"✅ Готово!\n\n"
            f"Теперь опубликуй пост в канале — через 20-30 секунд появится кнопка."
        )
        logging.info(f"✅ Пользователь {user_id} настроен")


async def main():
    load_settings()
    logging.info("🚀 Бот запущен. Напиши /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
