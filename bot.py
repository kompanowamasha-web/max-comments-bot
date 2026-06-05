import asyncio
import logging
import os

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return
    
    # Показываем все атрибуты объекта
    print("=" * 50)
    print("Доступные атрибуты event.message:")
    for attr in dir(event.message):
        if not attr.startswith('_'):  # Показываем только публичные атрибуты
            print(f"  - {attr}")
    
    print("\nПробуем получить ID разными способами:")
    
    # Пробуем разные варианты
    try:
        print(f"event.message.id: {event.message.id}")
    except AttributeError as e:
        print(f"event.message.id: ❌ {e}")
    
    try:
        print(f"event.message.message_id: {event.message.message_id}")
    except AttributeError as e:
        print(f"event.message.message_id: ❌ {e}")
    
    try:
        print(f"event.message.msg_id: {event.message.msg_id}")
    except AttributeError as e:
        print(f"event.message.msg_id: ❌ {e}")
    
    try:
        print(f"event.message.uuid: {event.message.uuid}")
    except AttributeError as e:
        print(f"event.message.uuid: ❌ {e}")
    
    # Показываем сам объект
    print(f"\nСодержимое event.message: {event.message}")
    print(f"Тип: {type(event.message)}")
    print("=" * 50)


async def main():
    print("Бот запущен. Отправьте сообщение в канал...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
