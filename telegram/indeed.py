# Пример запроса к базе знаний

# импорт модулей
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.ext import ContextTypes
from telegram import Update,  InlineKeyboardButton, InlineKeyboardMarkup                    
from dotenv import load_dotenv
import os
import requests
import aiohttp
import base64

# загружаем переменные окружения
load_dotenv()

# токен бота
TOKEN = os.getenv('TG_TOKEN')

# создаем кнопки
buttons = [
    InlineKeyboardButton('ICM', callback_data = 'ICM'),
    InlineKeyboardButton('IAM', callback_data = 'IAM'),    
]  

# форма inline клавиатуры
form_ver = True
if form_ver:    # если вертикальное расположение
    inline_frame = [
        [buttons[0]], [buttons[1]]
    ]
else:
    inline_frame = [
        [buttons[0], buttons[1]]
    ]    

# создаем inline клавиатуру
inline_keyboard = InlineKeyboardMarkup(inline_frame)


# функция-обработчик команды /start
async def start(update, context):

    # сообщение пользователю
    await update.message.reply_text("Привет! Я консультант компании ИНДИД!")
    # прикрепляем inline клавиатуру к сообщению
    await update.message.reply_text('По какому продукту у вас есть вопросы:', reply_markup=inline_keyboard)

# функция-обработчик нажатий на кнопки
async def button(update: Update, context):

    # получаем callback query из update
    query = update.callback_query

    # всплывающее уведомление
    await query.answer('Это всплывающее уведомление!')
    
    # Сохраняем callback_data в user_data
    context.user_data['selected_db'] = query.data
    
    context.user_data['chat_history'] = []  # Инициализируем историю
    
    # редактируем сообщение после нажатия
    await query.edit_message_text(text = f'Хорошо \n Задайте свой вопрос по базе: {query.data}')

# функция-обработчик текстовых сообщений
async def text(update, context):
    selected_db = context.user_data.get('selected_db')  
    history = context.user_data.setdefault('chat_history', [])
    
    # обращение к API база эмбеддингов
    param = {
        'text': update.message.text,
        'select_db': selected_db
     }    
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8000/api/get_answer_async', json = param) as response:
            # получение ответа от API
            answer = await response.json()
            
            response_text = answer['message']
            
            history.append(f'Пользователь: {update.message.text}')
            history.append(f'Бот: {response_text}')
            history[:] = history[-10:]  # Ограничиваем историю 10 сообщениями
            
            print(history)

            # ответ пользователю
            await update.message.reply_text(answer['message'])
    

# Функция срабатывает через заданный интервал времени
async def task(context: ContextTypes.DEFAULT_TYPE):

    # сброс счетчиков у всех пользователей
    if context.bot_data != {}:

        # проходим по всем пользователям в базе и обновляем их доступные запросы
        for key in context.bot_data:
            context.bot_data[key] = 3
        print('Запросы пользователей обновлены')

# функция "Запуск бота"
def main():

    # создаем приложение и передаем в него токен
    application = Application.builder().token(TOKEN).build()

    # запуск планировщика
    shedule = application.job_queue
    interval = 60 # интервал 60 секунд = 1 минута
    shedule.run_repeating(task, interval = interval) 

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler('start', start))

    # добавляем CallbackQueryHandler (для inline кнопок)
    application.add_handler(CallbackQueryHandler(button))

    # добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))

    # запускаем бота (нажать Ctrl-C для остановки бота)
    print('Бот запущен...')    
    application.run_polling()
    print('Бот остановлен')

# проверяем режим запуска модуля
if __name__ == "__main__":      # если модуль запущен как основная программа

    # запуск бота
    main()