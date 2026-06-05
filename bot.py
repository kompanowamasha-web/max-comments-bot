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
API_BASE_URL = "https://platform-api.max.ru"

bot = Bot(TOKEN)
dp = Dispatcher()

# Хранилище ссылок
discussion_urls = []


async def send_message_to_user(user_id: int, text: str):
    """Отправляет сообщение пользователю в личный чат."""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": TOKEN,
            "Content-Type": "application/json"
        }
        url = f"{API_BASE_URL}/messages"
        # Для личного чата используем user_id
        payload = {"user_id": user_id, "text": text}

        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                logging.info(f"✅ Сообщение отправлено пользователю {user_id}")
                return True
            else:
                error_text = await resp.text()
                logging.error(f"❌ Ошибка при отправке: {resp.status} - {error_text}")
                return False


async def add_button_to_message(message_id: str, discussion_url: str):
    """Добавляет кнопку к сообщению в канале."""
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
                logging.info(f"✅ Кнопка добавлена к посту {message_id}")
                return True
            else:
                error_text = await resp.text()
                logging.error(f"❌ Ошибка при добавлении кнопки: {resp.status} - {error_text}")
                return False


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    """Приветствие при команде /start."""
    # Получаем ID пользователя из recipient
    user_id = event.message.recipient.user_id
    
    text = (
        "👋 Привет!\n\n"
        "**⚠️ Важно:** Кнопка появляется в течение **20-30 секунд** после публикации поста. "
        "Это нормально, просто API MAX обрабатывает запрос с небольшой задержкой. Не переживай, всё работает! ⏱️\n\n"
        "**Для настройки:**\n"
        "1. Добавь меня в свой канал как **администратора**.\n"
        "2. Создай чат для обсуждений.\n"
        "3. Добавь меня в этот чат как **участника**.\n\n"
        "📎 **Отправь мне ссылку на чат для обсуждений**\n"
        "(например, https://max.ru/join/XXXXXXXX)"
    )
    
    await send_message_to_user(user_id, text)
    logging.info(f"Ответили пользователю {user_id}")


@dp.message_created()
async def handle_text(event: MessageCreated):
    """Сохраняет ссылку из сообщения пользователя."""
    # Проверяем, что это личный диалог с ботом
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return
    
    user_id = event.message.recipient.user_id
    text = event.message.body.text if event.message.body else ""
    
    # Ищем ссылку
    match = re.search(r'https://max\.ru/join/[\w-]+', text)
    if match:
        discussion_url = match.group(0)
        discussion_urls.append(discussion_url)
        await send_message_to_user(user_id, f"✅ Ссылка сохранена: {discussion_url}\n\nТеперь я готов! Когда ты опубликуешь пост в канале, я добавлю под ним кнопку 'Прокомментировать'. Кнопка появится в течение 20-30 секунд ⏱️")
    else:
        # Игнорируем всё, кроме команды /start и ссылок
        if not text.startswith('/'):
            await send_message_to_user(user_id, "❌ Не нашёл ссылку. Отправь ссылку в формате: https://max.ru/join/XXXXXXXX")


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    """Добавляет кнопку под новыми постами в канале."""
    # Проверяем, что это канал
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return
    
    # Берём первую сохранённую ссылку
    if not discussion_urls:
        logging.warning("Нет сохранённой ссылки")
        return
    
    discussion_url = discussion_urls[0]
    message_id = event.message.body.mid
    
    logging.info(f"📢 Новый пост в канале. Добавляем кнопку...")
    await add_button_to_message(message_id, discussion_url)


async def main():
    logging.info("🚀 Бот запущен. Напишите /start в личные сообщения")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
