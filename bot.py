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
API_BASE_URL = "https://platform-api.max.ru"

bot = Bot(TOKEN)
dp = Dispatcher()

# Ссылка по умолчанию (твоя)
DISCUSSION_URL = "https://max.ru/join/wy_GIFvYp606nOFaDZg6IpYs0hPOGY6itIbTj46kEso"


async def add_button_to_message(message_id: str, url: str):
    """Добавляет кнопку к посту в канале"""
    keyboard = {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {
                        "type": "link",
                        "text": "Прокомментировать",
                        "url": url
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
                logging.info(f"✅ Кнопка добавлена")
            else:
                error = await resp.text()
                logging.error(f"❌ Ошибка: {resp.status} - {error}")


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    """Приветствие и инструкция"""
    text = (
        "👋 Привет! Я бот Комментарии для канала. Я помогу тебе в твоём канале создать кнопочку под постом \"Прокомментировать\".\n\n"
        "Для настройки:\n"
        "1. Добавь меня в свой канал как администратора.\n"
        "2. Создай чат для обсуждений.\n"
        "3. Добавь меня в этот чат как администратора.\n\n"
        "Отправь мне ссылку на чат для обсуждений.\n"
        "Пример: https://max.ru/join/XXXXXXXX\n\n"
        "Важно: кнопка появляется в течение 20-30 секунд после публикации поста. "
        "Это нормально, API Max обрабатывает запрос с небольшой задержкой, не переживай."
    )
    await event.message.answer(text)


@dp.message_created()
async def handle_text(event: MessageCreated):
    """Сохраняет ссылку, если пользователь её отправил"""
    global DISCUSSION_URL
    
    # Проверяем, что это личный диалог с ботом
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return
    
    text = event.message.body.text if event.message.body else ""
    
    # Ищем ссылку в сообщении
    match = re.search(r'https://max\.ru/join/[\w-]+', text)
    if match:
        DISCUSSION_URL = match.group(0)
        await event.message.answer(f"✅ Ссылка сохранена!\n\nТеперь я буду добавлять кнопку \"Прокомментировать\" под твоими постами. Кнопка появляется через 20-30 секунд.")
    else:
        # Если это не команда /start и не ссылка — игнорируем
        if not text.startswith('/'):
            await event.message.answer("❌ Не нашёл ссылку. Отправь ссылку в формате: https://max.ru/join/XXXXXXXX")


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    """Добавляет кнопку под каждым новым постом в канале"""
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return

    message_id = event.message.body.mid
    logging.info(f"📢 Новый пост в канале, добавляем кнопку...")
    await add_button_to_message(message_id, DISCUSSION_URL)


async def main():
    logging.info("🚀 Бот запущен. Напиши /start в личные сообщения для настройки")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
