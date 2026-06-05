import asyncio
import logging
import os
import re

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, Command
from maxapi.enums.chat_type import ChatType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
bot = Bot(TOKEN)
dp = Dispatcher()

# Хранилище ссылки на чат для обсуждений
discussion_url = None


async def add_button_to_message(message_id: str, url: str):
    """Добавляет кнопку 'Прокомментировать' к посту в канале."""
    import aiohttp
    
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
        url_api = f"https://platform-api.max.ru/messages?message_id={message_id}"
        
        async with session.put(url_api, headers=headers, json={"attachments": [keyboard]}) as resp:
            if resp.status == 200:
                logging.info(f"✅ Кнопка добавлена к посту")
            else:
                error = await resp.text()
                logging.error(f"❌ Ошибка: {resp.status} - {error}")


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    """Приветствие — используем встроенный answer()"""
    global discussion_url
    
    text = (
        "👋 Привет!\n\n"
        "**⚠️ Важно:** Кнопка появляется в течение **20-30 секунд** после публикации поста. "
        "Это нормально, API MAX обрабатывает запрос с небольшой задержкой. Не переживай! ⏱️\n\n"
        "**Для настройки:**\n"
        "1. Добавь меня в свой канал как **администратора**.\n"
        "2. Создай чат для обсуждений.\n"
        "3. Добавь меня в этот чат как **участника**.\n\n"
        "📎 **Отправь мне ссылку на чат для обсуждений**\n"
        "Пример: `https://max.ru/join/XXXXXXXX`"
    )
    
    # ВСТРОЕННЫЙ МЕТОД — НЕ НУЖНО ПРИДУМЫВАТЬ ID
    await event.message.answer(text)


@dp.message_created()
async def handle_text(event: MessageCreated):
    """Сохраняет ссылку из сообщения пользователя."""
    global discussion_url
    
    # Проверяем, что это личный диалог с ботом
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return
    
    text = event.message.body.text if event.message.body else ""
    
    # Ищем ссылку в сообщении
    match = re.search(r'https://max\.ru/join/[\w-]+', text)
    if match:
        discussion_url = match.group(0)
        await event.message.answer(f"✅ Ссылка сохранена!\n\nТеперь я готов: когда ты опубликуешь пост в канале, я добавлю под ним кнопку 'Прокомментировать' (через 20-30 секунд) ⏱️")
    else:
        if not text.startswith('/'):
            await event.message.answer("❌ Не нашёл ссылку. Отправь ссылку в формате: https://max.ru/join/XXXXXXXX")


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    """Добавляет кнопку под новыми постами в канале."""
    global discussion_url
    
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return
    
    if not discussion_url:
        logging.warning("Нет сохранённой ссылки")
        return
    
    message_id = event.message.body.mid
    logging.info(f"📢 Новый пост в канале. Добавляем кнопку...")
    await add_button_to_message(message_id, discussion_url)


async def main():
    logging.info("🚀 Бот запущен. Напишите /start в личные сообщения")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
