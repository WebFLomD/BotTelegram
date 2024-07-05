import telebot
from telebot import types
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен Бота
TOKEN_BOT_TELEGRAM = '7335892711:AAHLoPwFkB1WRks4pITFylV8bARfKEOcZU4'

# Список администраторов (ID пользователей)
ADMIN_IDS = [964550681]

# Категории и пути к ним
CATEGORIES = {
    'html': 'data/html/',
    'css': 'data/css/',
    'yii': 'data/yii/'
}

# Инициализация бота
bot = telebot.TeleBot(TOKEN_BOT_TELEGRAM)

def create_inline_keyboard(buttons):
    markup = types.InlineKeyboardMarkup()
    for text, callback_data in buttons:
        markup.add(types.InlineKeyboardButton(text, callback_data=callback_data))
    return markup

def create_category_keyboard():
    return create_inline_keyboard([(category.upper(), category) for category in CATEGORIES.keys()])

def create_file_keyboard(category):
    markup = types.InlineKeyboardMarkup()
    try:
        files = os.listdir(CATEGORIES[category])
        if not files:
            markup.add(types.InlineKeyboardButton('Нет файлов', callback_data='no_files'))
        else:
            for file in files:
                markup.add(types.InlineKeyboardButton(file, callback_data=f'{category}:{file}'))
    except FileNotFoundError:
        markup.add(types.InlineKeyboardButton('Категория не найдена', callback_data='category_not_found'))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    buttons = [
        ('Категория', 'category'),
        ('Поддержать', 'support')
    ]
    markup = create_inline_keyboard(buttons)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! Выберите опцию:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    logger.info(f'Received callback query: {call.data}')
    if call.data == 'category':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите категорию:", reply_markup=create_category_keyboard())
    elif call.data == 'support':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вы выбрали Поддержать")
    elif call.data in CATEGORIES.keys():
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Выберите файл из категории {call.data.upper()}:', reply_markup=create_file_keyboard(call.data))
    elif ':' in call.data:
        category, file = call.data.split(':', 1)
        if category in CATEGORIES and file in os.listdir(CATEGORIES[category]):
            file_path = os.path.join(CATEGORIES[category], file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Содержимое файла {file}:\n\n{content}')
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                bot.answer_callback_query(call.id, "Ошибка при чтении файла")
        else:
            bot.answer_callback_query(call.id, "Файл не найден")
    else:
        bot.answer_callback_query(call.id, "Неизвестная команда")


@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_IDS)
def handle_admin_message(message):
    text = message.text
    if text.startswith('/post'):
        parts = text.split(' ')
        if len(parts) < 4:
            bot.reply_to(message, 'Используйте команду /post <категория> <имя_файла> <содержимое>')
            return
        _, category, filename, *content = parts
        content = ' '.join(content)
        if category in CATEGORIES:
            file_path = os.path.join(CATEGORIES[category], f'{filename}.txt')
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                bot.reply_to(message, f'Пост добавлен в категорию {category.upper()} с именем файла {filename}.txt')
            except Exception as e:
                logger.error(f"Error writing file {file_path}: {e}")
                bot.reply_to(message, f'Ошибка при добавлении поста в категорию {category.upper()} с именем файла {filename}.txt')
        else:
            bot.reply_to(message, 'Неверная категория')
    else:
        bot.reply_to(message, 'Используйте команду /post <категория> <имя_файла> <содержимое>')
        
bot.infinity_polling()