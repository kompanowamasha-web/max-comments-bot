import asyncio
import logging
import os

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message_created()
async def all_messages(event: MessageCreated):
    print("\n" + "=" * 60)
    print("🔍 Пришло сообщение в личку!")
    print(f"Тип чата: {event.message.recipient.chat_type}")
    print(f"chat_type как число: {event.message.recipient.chat_type.value if hasattr(event.message.recipient.chat_type, 'value') else 'не число'}")
    print(f"Текст: {event.message.body.text if event.message.body else 'нет текста'}")
    print(f"ID получателя: {event.message.recipient.user_id}")
    print(f"ID отправителя: {event.message.sender.user_id}")
    print("=" * 60)
    
    # Отправляем ответ
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text="Я получил твоё сообщение!"
    )


async def main():
    print("Бот запущен. Напиши ему что-нибудь в личку (и ссылку тоже)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
