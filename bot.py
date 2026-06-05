import asyncio
import logging
import os
import aiohttp

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
API_BASE_URL = "https://platform-api.max.ru"

bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return

    print("=" * 60)
    print("🔍 СООБЩЕНИЕ ИЗ КАНАЛА")
    print(f"chat_id: {event.message.recipient.chat_id}")
    print(f"message_id: {event.message.body.mid}")
    print(f"текст: {event.message.body.text}")
    print("=" * 60)
    
    # Пробуем добавить кнопку с тестовой ссылкой
    test_url = "https://max.ru/join/wy_GIFvYp606nOFaDZg6IpYs0hPOGY6itIbTj46kEso"
    
    keyboard = {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [[{"type": "link", "text": "Прокомментировать", "url": test_url}]]
        }
    }
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        url = f"{API_BASE_URL}/messages?message_id={event.message.body.mid}"
        
        async with session.put(url, headers=headers, json={"attachments": [keyboard]}) as resp:
            print(f"Статус ответа: {resp.status}")
            if resp.status == 200:
                print("✅ Кнопка добавлена!")
            else:
                error = await resp.text()
                print(f"❌ Ошибка: {error}")


async def main():
    print("Бот запущен. Отправь сообщение в канал...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
