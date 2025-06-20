import os
import time
from dotenv import load_dotenv
import json
from telethon import TelegramClient
from telethon.errors import UsernameNotOccupiedError, PeerIdInvalidError

load_dotenv()
API_ID = os.getenv("API_ID")        
API_HASH = os.getenv("API_HASH")    
SESSION_NAME = os.getenv("SESSION_NAME")    

# Инициализация клиента
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def load_broadcast_data():
    """Загружает данные для рассылки из файла."""
    try:
        with open("broadcast_data.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("Файл broadcast_data.json не найден. Запустите интерфейсный бот для его создания.")
        return None
    except json.JSONDecodeError:
        print("Ошибка чтения файла broadcast_data.json. Проверьте формат.")
        return None


async def send_messages():
    """Рассылка сообщений пользователям или в чаты."""
    # Загружаем данные из файла
    data = await load_broadcast_data()
    if not data:
        print("Не удалось загрузить данные для рассылки. Проверьте файл broadcast_data.json.")
        return

    usernames = data.get("usernames", [])
    message = data.get("message", "")
    schedule = data.get("schedule")
    quantity = list(data.get("quantity"))

    if not usernames or not message:
        print("Список пользователей или сообщение пусты.")
        return

    print("Начинаем рассылку сообщений...")
    for i in quantity:
        for username in usernames:
            try:
                # Получаем сущность пользователя/чата
                entity = await client.get_entity(username)
                await client.send_message(entity, message)
                print(f"Сообщение отправлено: {username}")
                time.sleep(0.2)
            except UsernameNotOccupiedError:
                print(f"Ошибка: Пользователь или чат {username} не найден.")
                time.sleep(0.2)
            except PeerIdInvalidError:
                print(f"Ошибка: Неверный ID для {username}.")
                time.sleep(0.2)
            except Exception as e:
                print(f"Не удалось отправить сообщение для {username}: {e}")
                time.sleep(0.2)      
        if quantity == 1:
            break 
        time.sleep(schedule*3600)

    print("Рассылка завершена!")


async def main():
    """Основной процесс."""
    async with client:
        await send_messages()


if __name__ == "__main__":
    print("Запуск бота-рассыльщика...")
    client.loop.run_until_complete(main())
# Добавить scheduler
# Добавить эрор лог

