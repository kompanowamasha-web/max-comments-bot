import asyncio
import logging
import os
import aiohttp

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated
from maxapi.types.attachments import AttachmentButton, ButtonsPayload, LinkButton
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
DISCUSSION_URL = "https://max.ru/join/wy_GIFvYp606nOFaDZg6IpYs0hPOGY6itIbTj46kEso"
API_BASE_URL = "https://platform-api.max.ru"

bot = Bot(TOKEN)
dp = Dispatcher()


async def edit_message_with_button(chat_id: int, message_id: str, button_url: str):
    """Редактирует сообщение через прямой API-запрос (как в документации MAX)"""
    
    # Формируем клавиатуру
    keyboard = {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {
                        "type": "link",
                        "text": "Прокомментировать",
                        "url": button_url
                    }
                ]
            ]
        }
    }
    
    # PUT-запрос согласно документации: /messages?message_id={message_id}
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


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    # Проверяем, что это сообщение в канале
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return

    chat_id = event.message.recipient.chat_id
    message_id = event.message.id
    
    # Добавляем кнопку под постом
    await edit_message_with_button(chat_id, message_id, DISCUSSION_URL)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
