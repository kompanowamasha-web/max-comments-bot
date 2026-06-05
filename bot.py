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

# Хранилище настроек для каждого пользователя
user_settings = {}


async def add_button_to_message(message_id: str, discussion_url: str):
    """Добавляет кнопку к посту в канале"""
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
        headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        url_api = f"{API_BASE_URL}/messages?message_id={message_id}"
        
        async with session.put(url_api, headers=headers, json={"attachments": [keyboard]}) as resp:
            if resp.status == 200:
                logging.info(f"✅ Кнопка добавлена")
                return True
            else:
                error = await resp.text()
                logging.error(f"❌ Ошибка: {resp.status} - {error}")
                return False


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    """ТОЛЬКО ДЛЯ ЛИЧНЫХ СООБЩЕНИЙ"""
    # Проверяем, что это личный диалог
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return
    
    user_id = event.message.sender.user_id
    
    if user_id not in user_settings:
        user_settings[user_id] = {}
    
    user_settings[user_id]["waiting_for"] = "channel_url"
    
    text = (
        "👋 Привет! Я бот Комментарии для канала.\n\n"
        "Давай настроим твоего бота.\n\n"
        "**Шаг 1 из 2:**\n"
        "Отправь мне **ссылку на твой канал**.\n\n"
        "Ссылка выглядит так: `https://max.ru/c/XXXXXXXX`"
    )
    await event.message.answer(text)


@dp.message_created()
async def handle_text(event: MessageCreated):
    """Обрабатывает ссылки ТОЛЬКО из личных сообщений"""
    # ✅ КЛЮЧЕВАЯ ПРОВЕРКА: игнорируем всё, что не из личного диалога
    if event.message.recipient.chat_type != ChatType.DIALOG:
        return
    
    user_id = event.message.sender.user_id
    text = event.message.body.text if event.message.body else ""
    
    if user_id not in user_settings:
        await event.message.answer("Напиши /start, чтобы начать настройку")
        return
    
    waiting_for = user_settings[user_id].get("waiting_for")
    
    url_match = re.search(r'https://max\.ru/(?:c|join)/[\w-]+', text)
    if not url_match:
        await event.message.answer("❌ Не нашёл ссылку")
        return
    
    url = url_match.group(0)
    
    if waiting_for == "channel_url":
        user_settings[user_id]["channel_url"] = url
        user_settings[user_id]["waiting_for"] = "discussion_url"
        await event.message.answer(
            f"✅ Ссылка на канал сохранена\n\n"
            f"**Шаг 2 из 2:**\n"
            f"Отправь мне **ссылку на чат для обсуждений**"
        )
    
    elif waiting_for == "discussion_url":
        if '/join/' not in url:
            await event.message.answer("❌ Это не ссылка на чат обсуждений")
            return
        
        user_settings[user_id]["discussion_url"] = url
        user_settings[user_id]["waiting_for"] = None
        
        await event.message.answer(
            f"✅ Готово!\n\n"
            f"Теперь опубликуй пост в канале — через 20-30 секунд появится кнопка."
        )
        logging.info(f"✅ Пользователь {user_id} настроен")


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    """Добавляет кнопку под постом в канале"""
    # Проверяем, что это канал
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return
    
    message_id = event.message.body.mid
    
    # Берём первую сохранённую ссылку (для бота одного пользователя)
    discussion_url = None
    for settings in user_settings.values():
        if settings.get("discussion_url"):
            discussion_url = settings["discussion_url"]
            break
    
    if not discussion_url:
        logging.warning("Нет сохранённой ссылки")
        return
    
    logging.info(f"📢 Новый пост. Добавляем кнопку...")
    await add_button_to_message(message_id, discussion_url)


async def main():
    logging.info("🚀 Бот запущен. Напиши /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
