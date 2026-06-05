import asyncio
import logging
import os

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated
from maxapi.types.attachments import AttachmentButton, ButtonsPayload, LinkButton
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
DISCUSSION_URL = "https://max.ru/join/wy_GIFvYp606nOFaDZg6IpYs0hPOGY6itIbTj46kEso"

bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    # Проверяем, что это сообщение в канале
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return

    # Получаем ID сообщения
    message_id = event.message.id
    chat_id = event.message.recipient.chat_id

    # Создаём кнопку
    keyboard = AttachmentButton(
        type="inline_keyboard",
        payload=ButtonsPayload(
            buttons=[
                [LinkButton(type="link", text="Прокомментировать", url=DISCUSSION_URL)]
            ]
        ),
    )

    # Редактируем сообщение, добавляя кнопку
    await bot.edit_message(
        message_id=message_id,
        attachments=[keyboard],
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
