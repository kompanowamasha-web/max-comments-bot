import asyncio
import logging
import os

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, Command

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    print("\n" + "=" * 60)
    print("🔍 ПОЛУЧЕНО СООБЩЕНИЕ")
    print("=" * 60)
    
    # Выводим всё содержимое event.message
    print(f"\n📦 event.message:")
    print(f"   {event.message}")
    
    print(f"\n📋 Все атрибуты event.message:")
    for attr in dir(event.message):
        if not attr.startswith('_'):
            try:
                value = getattr(event.message, attr)
                if not callable(value):
                    print(f"   - {attr}: {value}")
            except:
                pass
    
    print(f"\n👤 recipient:")
    for attr in dir(event.message.recipient):
        if not attr.startswith('_'):
            try:
                value = getattr(event.message.recipient, attr)
                if not callable(value):
                    print(f"   - {attr}: {value}")
            except:
                pass
    
    print(f"\n✉️ sender:")
    for attr in dir(event.message.sender):
        if not attr.startswith('_'):
            try:
                value = getattr(event.message.sender, attr)
                if not callable(value):
                    print(f"   - {attr}: {value}")
            except:
                pass
    
    print("=" * 60 + "\n")


async def main():
    print("Бот запущен. Напишите /start в личные сообщения")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
