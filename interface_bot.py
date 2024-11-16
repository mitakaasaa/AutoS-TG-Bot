
import os
import json
import subprocess
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загрузка токена из переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  

# Хранилище данных
data_store = {
    "usernames": [],
    "message": "",
    "schedule": 1,
    "quantity": 1
}

# Главное меню
MAIN_MENU = ReplyKeyboardMarkup(
    [["Добавить пользователей", "Ввести сообщение"], ["Начать рассылку", "Сброс"], ["Установить частоту отправки"],["Установить кол-во отправок"]],
    resize_keyboard=True
)


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка, является ли пользователь администратором."""
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этому боту.")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start. Приветствие и проверка доступа."""
    if not await check_admin(update, context):
        return

    await update.message.reply_text(
        "Привет! Вы авторизованы. Выберите действие:", reply_markup=MAIN_MENU
    )


async def add_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление пользователей."""
    if not await check_admin(update, context):
        return

    await update.message.reply_text("Введите список пользователей или чатов через пробел:")
    context.user_data["awaiting"] = "usernames"


async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка сообщения для рассылки."""
    if not await check_admin(update, context):
        return

    await update.message.reply_text("Введите сообщение для рассылки:")
    context.user_data["awaiting"] = "message"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений."""
    if not await check_admin(update, context):
        return

    if context.user_data.get("awaiting") == "usernames":
        # Сохраняем список пользователей
        usernames = update.message.text.split()
        data_store["usernames"] = usernames
        context.user_data["awaiting"] = None
        await update.message.reply_text(f"Добавлены пользователи: {', '.join(usernames)}", reply_markup=MAIN_MENU)

    elif context.user_data.get("awaiting") == "message":
        # Сохраняем сообщение
        message = update.message.text
        data_store["message"] = message
        context.user_data["awaiting"] = None
        await update.message.reply_text(f"Сообщение установлено:\n\n{message}", reply_markup=MAIN_MENU)

    elif context.user_data.get("awaiting") == "schedule":
        try:
            if int(update.message.text) in range(1,10):
                schedule = int(update.message.text)
                data_store["schedule"] = schedule
                context.user_data["awaiting"] = None
                await update.message.reply_text(f"Установлен интервал:{schedule}",reply_markup=MAIN_MENU)
            else:
                await update.message.reply_text("Интервал не установлен! попробуйте ещё раз",reply_markup=MAIN_MENU)
                context.user_data["awaiting"] = None
        except Exception as e:
            await update.message.reply_text(f"Интервал не установлен: {e}\nВы можете попробовать ещё раз",reply_markup=MAIN_MENU) 

    elif context.user_data.get("awaiting") == "quantity":
        try:
            if int(update.message.text) in range(1,1000):
                quantity = int(update.message.text)
                data_store["quantity"] = quantity
                context.user_data["awaiting"] = None
                await update.message.reply_text(f"Установлено количество отправок: {quantity}", reply_markup=MAIN_MENU)
            else:
                await update.message.reply_text("Максимальное количество превышено! Допустимое максимальное кол-во: 999 отправок", reply_markup=MAIN_MENU)
        except Exception as e:
            await update.message.reply_text("Количество отправок не установлено: {e}", reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text("Я не понял. Выберите действие из меню.", reply_markup=MAIN_MENU)


async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Инициализация рассылки."""
    if not await check_admin(update, context):
        return

    if not data_store["usernames"]:
        await update.message.reply_text("Список пользователей пуст. Добавьте пользователей.")
        return

    if not data_store["message"]:
        await update.message.reply_text("Сообщение не установлено. Введите сообщение.")
        return

    await update.message.reply_text(f"Кол-во отправок: {data_store['quantity']}, Интервал: раз в {data_store['schedule']} час(а)\n Сообщение:{data_store['message']}\n\n ОТправить? Да/Нет:")
    if update.message.text not in ["Yes","Si","Ja","yes","si","ja","Да","да"]:
        await update.message.reply_text("Отмена")
        return

    # Сохраняем данные для рассылки в файл
    with open("broadcast_data.json", "w") as f:
        json.dump(data_store, f)

    await update.message.reply_text("Сообщение сохранено! Начинаю рассылку...")
    subprocess.Popen(['python', 'main_bot.py'])


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сброс данных."""
    if not await check_admin(update, context):
        return

    data_store["usernames"] = []
    data_store["message"] = ""
    await update.message.reply_text("Данные сброшены.", reply_markup=MAIN_MENU)


async def set_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await check_admin(update, context):
        return
    
    await update.message.reply_text("Установите интервал(например: каждый час - 1, каждые 2 часа - 2 и т.д.): ")
    context.user_data["awaiting"] = "schedule"

async def set_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update, context):
        return
    
    await update.message.reply_text("Установите количество отправок(Целое число, максимум 999):")
    context.user_data["awaiting"] = "quantity"



def main() -> None:
    """Запуск бота."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(["Добавить пользователей"]), add_usernames))
    app.add_handler(MessageHandler(filters.Text(["Ввести сообщение"]), set_message))
    app.add_handler(MessageHandler(filters.Text(["Начать рассылку"]), start_broadcast))
    app.add_handler(MessageHandler(filters.Text(["Сброс"]), reset))
    app.add_handler(MessageHandler(filters.Text(["Установить интервал"]),set_schedule))
    app.add_handler(MessageHandler(filters.Text(["Установить кол-во отправок"]),set_quantity))

    # Обработка текста
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск
    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
