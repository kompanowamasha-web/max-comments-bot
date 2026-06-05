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
DISCUSSION_URL = "https://max.ru/join/wy_GIFvYp606nOFaDZg6IpYs0hPOGY6itIbTj46kEso"  # ← ССЫЛКА ПО УМОЛЧАНИЮ
API_BASE_URL = "https://platform-api.max.ru"

bot = Bot(TOKEN)
dp = Dispatcher()


async def add_button_to_message(message_id: str, discussion_url: str):
    """Добавляет кнопку к сообщению"""
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
        headers = {
            "Authorization": TOKEN,
            "Content-Type": "application/json"
        }
        url = f"{API_BASE_URL}/messages?message_id={message_id}"
        payload = {"attachments": [keyboard]}
        
        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                logging.info(f"✅ Кнопка добавлена в сообщение {message_id}")
            else:
                error_text = await resp.text()
                logging.error(f"❌ Ошибка {resp.status}: {error_text}")


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
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
    """Сохраняет ссылку из сообщения пользователя и перезаписывает DISCUSSION_URL"""
    global DISCUSSION_URL
    
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return
    
    text = event.message.body.text if event.message.body else ""
    
    # Ищем ссылку в сообщении
    match = re.search(r'https://max\.ru/join/[\w-]+', text)
    if match:
        DISCUSSION_URL = match.group(0)  # ← ПЕРЕЗАПИСЫВАЕМ ГЛОБАЛЬНУЮ ПЕРЕМЕННУЮ
        await event.message.answer(f"✅ Ссылка сохранена: {DISCUSSION_URL}\n\nТеперь я готов! Когда ты опубликуешь пост в канале, я добавлю под ним кнопку \"Прокомментировать\" (через 20-30 секунд)")
    else:
        if not text.startswith('/'):
            await event.message.answer("❌ Не нашёл ссылку. Отправь ссылку в формате: https://max.ru/join/XXXXXXXX")


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return

    message_id = event.message.body.mid
    logging.info(f"Получено сообщение в канале. ID: {message_id}")
    await add_button_to_message(message_id, DISCUSSION_URL)  # ← ПЕРЕДАЁМ ССЫЛКУ


async def main():
    logging.info("Бот запущен. Напишите /start в личные сообщения")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
