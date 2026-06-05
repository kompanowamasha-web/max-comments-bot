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
# Ключ: user_id, значение: {"channel_url": "...", "discussion_url": "..."}
user_settings = {}


async def add_button_to_message(channel_id: int, message_id: str, discussion_url: str):
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
                logging.info(f"✅ Кнопка добавлена в канал {channel_id}")
                return True
            else:
                error = await resp.text()
                logging.error(f"❌ Ошибка API: {resp.status} - {error}")
                return False


@dp.message_created(Command('start'))
async def start_command(event: MessageCreated):
    """Начало настройки — запрашиваем ссылку на канал"""
    user_id = event.message.sender.user_id
    chat_id = event.message.recipient.chat_id
    
    # Инициализируем настройки пользователя
    if user_id not in user_settings:
        user_settings[user_id] = {}
    
    # Переводим пользователя в режим ожидания ссылки на канал
    user_settings[user_id]["waiting_for"] = "channel_url"
    
    text = (
        "👋 Привет! Я бот Комментарии для канала.\n\n"
        "Давай настроим твоего бота.\n\n"
        "**Шаг 1 из 2:**\n"
        "Отправь мне **ссылку на твой канал**.\n\n"
        "Ссылка выглядит так: `https://max.ru/c/XXXXXXXX`\n\n"
        "Где её взять:\n"
        "- Открой свой канал в MAX\n"
        "- Нажми на аватар → Поделиться → Копировать ссылку"
    )
    await event.message.answer(text)


@dp.message_created()
async def handle_text(event: MessageCreated):
    """Обрабатывает отправленные пользователем ссылки"""
    user_id = event.message.sender.user_id
    
    # Проверяем, что это личный диалог
    if str(event.message.recipient.chat_type) != 'dialog':
        return
    
    # Если пользователь не в процессе настройки — игнорируем
    if user_id not in user_settings:
        await event.message.answer("Напиши /start, чтобы начать настройку")
        return
    
    text = event.message.body.text if event.message.body else ""
    waiting_for = user_settings[user_id].get("waiting_for")
    
    # Ищем ссылку в тексте
    url_match = re.search(r'https://max\.ru/(?:c|join)/[\w-]+', text)
    if not url_match:
        await event.message.answer("❌ Не нашёл ссылку. Отправь ссылку в формате: https://max.ru/c/XXXXXXXX или https://max.ru/join/XXXXXXXX")
        return
    
    url = url_match.group(0)
    
    # Шаг 1: ждём ссылку на канал
    if waiting_for == "channel_url":
        user_settings[user_id]["channel_url"] = url
        user_settings[user_id]["waiting_for"] = "discussion_url"
        
        await event.message.answer(
            f"✅ Ссылка на канал сохранена: {url}\n\n"
            f"**Шаг 2 из 2:**\n"
            f"Отправь мне **ссылку на чат для обсуждений**.\n\n"
            f"Ссылка выглядит так: `https://max.ru/join/XXXXXXXX`"
        )
    
    # Шаг 2: ждём ссылку на чат обсуждений
    elif waiting_for == "discussion_url":
        # Проверяем, что это ссылка на приглашение (join)
        if '/join/' not in url:
            await event.message.answer("❌ Это не ссылка на чат обсуждений. Отправь ссылку с /join/")
            return
        
        user_settings[user_id]["discussion_url"] = url
        user_settings[user_id]["waiting_for"] = None
        
        channel_url = user_settings[user_id].get("channel_url")
        
        await event.message.answer(
            f"✅ Всё готово!\n\n"
            f"📌 Канал: {channel_url}\n"
            f"💬 Обсуждения: {url}\n\n"
            f"Теперь:\n"
            f"1. Убедись, что я добавлен в твой канал как **администратор**\n"
            f"2. Опубликуй пост в канале\n"
            f"3. Через 20-30 секунд под постом появится кнопка \"Прокомментировать\"\n\n"
            f"⚠️ Кнопка появляется с задержкой — это нормально, API MAX обрабатывает запрос не мгновенно."
        )
        
        logging.info(f"✅ Пользователь {user_id} настроил бота: канал {channel_url}, чат {url}")


@dp.message_created()
async def on_channel_post(event: MessageCreated):
    """Добавляет кнопку под постом в канале"""
    # Проверяем, что это канал
    if event.message.recipient.chat_type != ChatType.CHANNEL:
        return
    
    channel_id = event.message.recipient.chat_id
    message_id = event.message.body.mid
    
    # Получаем ссылку на канал из сообщения (чтобы понять, какой это канал)
    # В MAX API в событии может не быть прямой ссылки на канал, поэтому
    # нам нужно найти пользователя, который настроил этот канал.
    # Для простоты будем использовать первую найденную настройку
    # (для бота одного пользователя этого достаточно)
    
    # Находим настройки для этого канала
    discussion_url = None
    for user_id, settings in user_settings.items():
        channel_url = settings.get("channel_url")
        if channel_url and str(channel_id) in channel_url:
            discussion_url = settings.get("discussion_url")
            break
    
    if not discussion_url:
        logging.warning(f"⚠️ Нет настроек для канала {channel_id}")
        return
    
    logging.info(f"📢 Новый пост в канале {channel_id}. Добавляем кнопку...")
    await add_button_to_message(channel_id, message_id, discussion_url)


async def main():
    logging.info("🚀 Бот запущен. Напиши /start в личные сообщения для настройки")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
