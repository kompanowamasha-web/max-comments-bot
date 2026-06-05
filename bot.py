import asyncio
import logging
import os
import aiohttp

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
DISCUSSION_URL = "https://max.ru/join/wy_GIFvYp606nOFaDZg6IpYs0hPOGY6itIbTj46kEso"
API_BASE_URL = "https://platform-api.max.ru"

bot = Bot(TOKEN)
dp = Dispatcher()


async def add_button_to_message(message_id: str):
    """
    Добавляет кнопку к сообщению через прямой API-запрос.
    Соответствует официальной документации MAX API.
    """
    # Формируем inline-клавиатуру с кнопкой-ссылкой
    keyboard = {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {
                        "type": "link",
                        "text": "Прокомментировать",
                        "url": DISCUSSION_URL
                    }
                ]
            ]
        }
    }
    
    # Отправляем PUT-запрос согласно документации
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": TOKEN,
            "Content-Type": "application/json"
        }
        # message_id передаётся как query-параметр
        url = f"{API_BASE_URL}/messages?message_id={message_id}"
        # В теле запроса — только то, что меняем (attachments)
        payload = {"attachments": [keyboard]}
        
        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                logging.info(f"✅ Кнопка добавлена в сообщение {message_id}")
                return True
            else:
                error_text = await resp.text()
                logging.error(f"❌ Ошибка {resp.status}: {error_text}")
                return False


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    # Проверяем, что это сообщение в канале
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        logging.info("Сообщение не из канала, пропускаем")
        return

    # Получаем ID сообщения (из предыдущих тестов мы знаем, что он в body.mid)
    message_id = event.message.body.mid
    logging.info(f"Получено сообщение в канале. ID: {message_id}")
    
    # Добавляем кнопку
    await add_button_to_message(message_id)


async def main():
    logging.info("Бот запущен. Ожидаю сообщения в канале...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
