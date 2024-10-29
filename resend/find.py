from pyrogram import Client

# Указываем API ID и API Hash
api_id = 21564722
api_hash = 'a37810f1f9432966784ac36e1df673bd'

app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Функция для получения списка каналов и их ID
async def list_channels(client):
    print("Начинаем проверку диалогов...")
    async for dialog in client.get_dialogs():

        channel_name = dialog.chat.title
        channel_id = dialog.chat.id
        print(f"Название канала: {channel_name}, ID: {channel_id}")
    print("Проверка завершена.")

# Запуск программы
async def main():
    async with app:
        await list_channels(app)

app.run(main())
