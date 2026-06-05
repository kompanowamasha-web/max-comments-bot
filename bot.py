import asyncio
import logging
import os

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated
from maxapi.types.attachments import InlineKeyboard, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
DISCUSSION_URL = "https://max.ru/join/wy_GIFvYp606nOFaDZg6IpYs0hPOGY6itIbTj46kEso"

bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    # Реагируем только на сообщения в канале (не на личку и не на группы)
    if not event.message.channel:
        return

    chat_id = event.message.chat_id
    message_id = event.message.id

    keyboard = InlineKeyboard(
        buttons=[
            [
                InlineKeyboardButton(
                    type="link",
                    text="Прокомментировать",
                    url=DISCUSSION_URL,
                )
            ]
        ]
    )

    await bot.edit_message(
        chat_id=chat_id,
        message_id=message_id,
        attachments=[keyboard],
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
