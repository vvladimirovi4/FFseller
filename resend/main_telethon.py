from pyrogram import Client, filters
from pyrogram.types import Message

# Указываем API ID и API Hash
api_id = 21564722
api_hash = 'a37810f1f9432966784ac36e1df673bd'

# Инициализируем клиент
app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Список ключевых слов для фильтрации сообщений
keywords = ["фулфилмент", "прайс", "расценки", "доставка"]

# Функция для поиска канала, в котором аккаунт является администратором
async def get_admin_channel(client: Client):
    async for dialog in client.get_dialogs():
        if dialog.chat.type == "channel" and dialog.chat.is_creator:
            return dialog.chat.id
    return None

# Переменная для хранения ID канала администратора
admin_channel_id = None

# Инициализация ID канала перед обработкой сообщений
@app.on_message()
async def initialize_channel(client: Client, message: Message):
    global admin_channel_id
    if admin_channel_id is None:  # Канал еще не инициализирован
        admin_channel_id = await get_admin_channel(client)
        if admin_channel_id is None:
            print("Канал, где вы являетесь администратором, не найден.")
            return

# Обработчик сообщений для пересылки в канал при наличии ключевых слов
@app.on_message()
async def forward_to_channel(client, message: Message):
    global admin_channel_id
    if admin_channel_id and message.text:
        # Проверяем, есть ли ключевые слова в тексте сообщения
        if any(keyword.lower() in message.text.lower() for keyword in keywords):
            await message.forward(admin_channel_id)

# Запуск бота
app.run()
