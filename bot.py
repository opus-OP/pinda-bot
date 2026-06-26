import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

# ============================================
#  ЗАГРУЗКА НАСТРОЕК ИЗ .env ФАЙЛА
# ============================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL"))
DEST_CHAT_ID = int(os.getenv("DEST_CHAT"))

# ============================================
#  НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================
#  ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================
#  ФУНКЦИЯ ПРОВЕРКИ, МОЖНО ЛИ КОПИРОВАТЬ СООБЩЕНИЕ
# ============================================
def is_copyable(message: types.Message) -> bool:
    """Возвращает True, если сообщение можно скопировать через copy_to"""
    if message.text:
        return True
    if message.photo:
        return True
    if message.video:
        return True
    if message.document:
        return True
    if message.audio:
        return True
    if message.voice:
        return True
    if message.sticker:
        return True
    if message.animation:
        return True
    if message.contact:
        return True
    if message.location:
        return True
    if message.poll:
        return True
    if message.game:
        return True
    if message.video_note:
        return True
    if message.invoice:
        return True
    if message.successful_payment:
        return True
    
    # Исключаем служебные сообщения
    if message.new_chat_members:
        return False
    if message.left_chat_member:
        return False
    if message.pinned_message:
        return False
    if message.connected_website:
        return False
    if message.proximity_alert_triggered:
        return False
    
    return False

# ============================================
#  ОСНОВНОЙ ОБРАБОТЧИК
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
        logger.error(f"❌ Ошибка API при пересылке ID {message.message_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при пересылке ID {message.message_id}: {e}")

# ============================================
#  КОМАНДЫ
# ============================================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🤖 Бот успешно запущен!\n\n"
        f"📡 Отслеживаю канал: `{SOURCE_CHANNEL_ID}`\n"
        f"📤 Пересылаю в чат: `{DEST_CHAT_ID}`\n\n"
        "Все новые сообщения из канала будут автоматически скопированы в указанный чат.",
        parse_mode="Markdown"
    )

@dp.message(Command("getid"))
async def get_id_cmd(message: types.Message):
    await message.answer(
        f"📌 ID этого чата: `{message.chat.id}`\n"
        f"📋 Тип чата: `{message.chat.type}`",
        parse_mode="Markdown"
    )

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    await message.answer(
        "📊 **Текущие настройки бота:**\n\n"
        f"📡 Канал-источник: `{SOURCE_CHANNEL_ID}`\n"
        f"📤 Чат-приёмник: `{DEST_CHAT_ID}`\n"
        f"🔄 Статус: Активен\n"
        f"⏱ Работает с момента запуска",
        parse_mode="Markdown"
    )

# ============================================
#  ЗАПУСК
# ============================================
async def main():
    logger.info("🚀 Бот запущен!")
    logger.info(f"📡 Источник: {SOURCE_CHANNEL_ID}")
    logger.info(f"📤 Приёмник: {DEST_CHAT_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())