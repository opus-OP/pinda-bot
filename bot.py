import subprocess
import sys
import os

# ============================================
#  АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ
# ============================================
def install_dependencies():
    try:
        import aiogram, dotenv, aiohttp
        try:
            import aiohttp_socks
        except ImportError:
            print("🔄 Устанавливаю aiohttp-socks...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp-socks"])
    except ImportError:
        print("🔄 Устанавливаю зависимости из requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

install_dependencies()

# ============================================
#  ИМПОРТЫ
# ============================================
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession  # <--- правильный импорт
from dotenv import load_dotenv
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

# ============================================
#  ЗАГРУЗКА .env
# ============================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL")) if os.getenv("SOURCE_CHANNEL") else None
DEST_CHAT_ID = int(os.getenv("DEST_CHAT")) if os.getenv("DEST_CHAT") else None
PROXY_URL = os.getenv("PROXY_URL")

if not BOT_TOKEN or SOURCE_CHANNEL_ID is None or DEST_CHAT_ID is None:
    print("❌ Ошибка: не заполнен .env файл!")
    print("Создайте .env с содержимым:")
    print("BOT_TOKEN=ваш_токен")
    print("SOURCE_CHANNEL=-1004440681402")
    print("DEST_CHAT=-1002203234805")
    print("PROXY_URL=socks5://127.0.0.1:1443")
    sys.exit(1)

# ============================================
#  ЛОГГЕР
# ============================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ============================================
#  ФУНКЦИЯ ПРОВЕРКИ КОПИРУЕМОСТИ
# ============================================
def is_copyable(message: types.Message) -> bool:
    if message.text or message.photo or message.video or message.document or \
       message.audio or message.voice or message.sticker or message.animation or \
       message.contact or message.location or message.poll or message.game or \
       message.video_note or message.invoice or message.successful_payment:
        return True
    if message.new_chat_members or message.left_chat_member or \
       message.pinned_message or message.connected_website or \
       message.proximity_alert_triggered:
        return False
    return False

# ============================================
#  СОЗДАНИЕ БОТА С ПРОКСИ
# ============================================
async def create_bot_and_dispatcher():
    if PROXY_URL:
        if PROXY_URL.startswith("socks"):
            connector = ProxyConnector.from_url(PROXY_URL)
        else:
            from aiohttp import TCPConnector
            connector = TCPConnector(proxy=PROXY_URL)
        aiohttp_session = ClientSession(connector=connector)
        aiogram_session = AiohttpSession(session=aiohttp_session)  # <--- правильное имя класса
    else:
        aiogram_session = None

    bot = Bot(token=BOT_TOKEN, session=aiogram_session)
    dp = Dispatcher()

    # ============================================
    #  РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
    # ============================================
    @dp.channel_post()
    async def forward_from_channel(message: types.Message):
        if message.chat.id != SOURCE_CHANNEL_ID:
            return
        if not is_copyable(message):
            logger.info(f"Пропускаем служебное сообщение ID {message.message_id}")
            return
        try:
            await message.copy_to(chat_id=DEST_CHAT_ID)
            logger.info(f"✅ Переслано сообщение ID {message.message_id}")
        except TelegramBadRequest as e:
            logger.error(f"❌ Ошибка API: {e}")
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка: {e}")

    @dp.message(Command("start"))
    async def start_cmd(message: types.Message):
        await message.answer(
            "🤖 Бот успешно запущен!\n\n"
            f"📡 Канал: `{SOURCE_CHANNEL_ID}`\n"
            f"📤 Чат: `{DEST_CHAT_ID}`\n"
            f"🔐 Прокси: `{PROXY_URL if PROXY_URL else 'Нет'}`",
            parse_mode="Markdown"
        )

    @dp.message(Command("getid"))
    async def get_id_cmd(message: types.Message):
        await message.answer(f"📌 ID этого чата: `{message.chat.id}`", parse_mode="Markdown")

    @dp.message(Command("stats"))
    async def stats_cmd(message: types.Message):
        await message.answer(
            "📊 **Настройки:**\n\n"
            f"📡 Источник: `{SOURCE_CHANNEL_ID}`\n"
            f"📤 Приёмник: `{DEST_CHAT_ID}`\n"
            f"🔐 Прокси: `{PROXY_URL or 'Отключён'}`\n"
            f"🔄 Статус: Активен",
            parse_mode="Markdown"
        )

    return bot, dp

# ============================================
#  ЗАПУСК
# ============================================
async def main():
    bot, dp = await create_bot_and_dispatcher()
    logger.info("🚀 Бот запущен!")
    logger.info(f"📡 Источник: {SOURCE_CHANNEL_ID}")
    logger.info(f"📤 Приёмник: {DEST_CHAT_ID}")
    logger.info(f"🔐 Прокси: {PROXY_URL if PROXY_URL else 'Нет'}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())