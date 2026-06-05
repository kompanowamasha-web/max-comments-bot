import asyncio
import logging
import os
import aiohttp
import re

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, Command
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
user_settings = {}

API_BASE_URL = "https://platform-api.max.ru"

bot = Bot(TOKEN)
dp = Dispatcher()


async def add_button_to_message(message_id: str, discussion_url: str):
    """Добавляет кнопку 'Прокомментировать' к сообщению в канале."""
    keyboard = {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {
                        "type": "link",
                        "text": "Прокомментировать",  # ← ИСПРАВЛЕНО: "Прокомментировать"
                        "url": discussion_url
                    }
                ]
            ]
        }
    }

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": TOKEN,
            "Content-Type": "application/json"
        }
        url = f"{API_BASE_URL}/messages?message_id={message_id}"
        payload = {"attachments": [keyboard]}

        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                logging.info(f"✅ Кнопка добавлена к посту {message_id}")
                return True
            else:
                error_text = await resp.text()
                logging.error(f"❌ Ошибка при добавлении кнопки: {resp.status} - {error_text}")
                return False


async def send_message(chat_id: int, text: str):
    """Отправляет сообщение в чат."""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": TOKEN,
            "Content-Type": "application/json"
        }
        url = f"{API_BASE_URL}/messages"
        payload = {"chat_id": chat_id, "text": text}

        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logging.error(f"❌ Ошибка при отправке сообщения: {resp.status} - {error_text}")


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    """Приветствие и начало настройки."""
    user_id = event.message.sender.id
    chat_id = event.message.recipient.chat_id

    welcome_text = (
        "👋 Привет! Я бот, который поможет добавить кнопку 'Прокомментировать' под постами в твоём канале.\n\n"
        "**⚠️ Важно:** Кнопка появляется в течение **20-30 секунд** после публикации поста. "
        "Это нормально, просто API MAX обрабатывает запрос с небольшой задержкой. Не переживай, всё работает! ⏱️\n\n"
        "**Для начала настройки:**\n"
        "1. Добавь меня в свой канал как **администратора**.\n"
        "2. Создай чат, в который будут вести комментарии.\n"
        "3. Добавь меня в этот чат как **участника** (администратор не обязателен).\n\n"
        "После этого отправь мне **ссылку на чат для обсуждений**.\n"
        "Ссылка выглядит так: `https://max.ru/join/XXXXXXXX`"
    )
    await send_message(chat_id, welcome_text)
    user_settings[user_id] = {"waiting_for": "discussion_link"}


@dp.message_created()
async def handle_text(event: MessageCreated):
    """Обрабатывает текстовые сообщения от пользователя."""
    user_id = event.message.sender.id
    chat_id = event.message.recipient.chat_id
    text = event.message.body.text if event.message.body else ""

    if user_id in user_settings and user_settings[user_id].get("waiting_for") == "discussion_link":
        match = re.search(r'https://max\.ru/join/[\w-]+', text)
        if match:
            discussion_url = match.group(0)
            user_settings[user_id]["discussion_url"] = discussion_url
            user_settings[user_id]["waiting_for"] = None
            await send_message(chat_id, f"✅ Ссылка сохранена: {discussion_url}\n\nТеперь я готов! Когда ты опубликуешь пост в канале, я добавлю под ним кнопку 'Прокомментировать'. Кнопка появится в течение 20-30 секунд ⏱️")
        else:
            await send_message(chat_id, "❌ Не удалось найти ссылку. Пожалуйста, отправь ссылку на чат для обсуждений в правильном формате (например, https://max.ru/join/XXXXXXXX).")
        return


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    """Добавляет кнопку под новыми постами в канале."""
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return

    channel_id = event.message.recipient.chat_id
    discussion_url = None
    for settings in user_settings.values():
        if settings.get("discussion_url"):
            discussion_url = settings["discussion_url"]
            break
    
    if not discussion_url:
        logging.warning(f"Нет настроек для канала {channel_id}. Игнорируем.")
        return
        
    message_id = event.message.body.mid
    logging.info(f"📢 Новый пост в канале. ID: {message_id}")
    await add_button_to_message(message_id, discussion_url)


async def main():
    logging.info("🚀 Бот запущен и готов к настройке через команду /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
