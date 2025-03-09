# импорт библиотек
from dotenv import load_dotenv                              # работа с переменными окружения
import os                                                   # взаимодействие с операционной системой
from openai import OpenAI                                   # взаимодействие с OpenAI API
from openai import AsyncOpenAI                              # асинхронное взаимодействие с OpenAI API
from langchain.text_splitter import CharacterTextSplitter   # библиотека langchain
from langchain.docstore.document import Document            # объект класса Document
from langchain_community.vectorstores import FAISS          # работа с векторной базой FAISS
from langchain_openai import OpenAIEmbeddings               # класс для работы с ветроной базой
from fastapi import HTTPException                           # для генерации исключений
from fastapi import status                                  # проверка статуса
import aiohttp
import time
import json

# получим переменные окружения из .env
load_dotenv('api/.env')

# класс для работы с OpenAI
class Chunk():
    
    # МЕТОД: инициализация
    def __init__(self):
        # загружаем базу знаний
        self.base_load()
        self.chat_history = []  # История сообщений

    # МЕТОД: загрузка базы знаний
    def base_load(self):
        
        # Указываем путь к сохранённой базе данных
        load_path = "api/base/FAISS_ICM"
        embeddings = OpenAIEmbeddings(
             api_key="sk-or-vv-97eb792c85f0c225413a6e7ff5115b3629e227c0ff69ff32006b17960dc8e530", # ваш ключ в VseGPT после регистрации
             openai_api_base="https://api.vsegpt.ru/v1",
             )

        # Загружаем базу данных FAISS из локального файла
        db_ICM = FAISS.load_local(load_path, embeddings,allow_dangerous_deserialization=True)
        self.db_ICM  =db_ICM

        # Указываем путь к сохранённой базе данных
        load_path = "api/base/FAISS_IAM"
        embeddings = OpenAIEmbeddings(
             api_key="sk-or-vv-97eb792c85f0c225413a6e7ff5115b3629e227c0ff69ff32006b17960dc8e530", # ваш ключ в VseGPT после регистрации
             openai_api_base="https://api.vsegpt.ru/v1",
             )

        # Загружаем базу данных FAISS из локального файла
        db_IAM = FAISS.load_local(load_path, embeddings,allow_dangerous_deserialization=True)

        self.db_IAM = db_IAM

        # формируем инструкцию system
        self.system = '''
            Очень подробно и детально ответь на вопрос пользователя,
            опираясь точно на документ с информацией для ответа клиенту.
            Не придумывай ничего от себя. Не ссылайся на сами отрывки документа
            с информацией для ответа, клиент о них ничего не должен знать.            
            '''   

    # МЕТОД: запрос к OpenAI синхронный
    def get_answer(self, query: str):
        
        
        
        # получаем релевантные отрезки из базы знаний
        docs = self.db.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        # формируем инструкцию user
        user = f'''
           Ответь на вопрос пользователя, но не упоминай данные тебе документы с информацией в ответе.
            Документ с информацией для ответа пользователю: {message_content}\n\n
            Вопрос пользователя: \n{query}
        '''
        # готовим промпт
        messages = [
            {'role': 'system', 'content': self.system},
            {'role': 'user', 'content': user}
        ]
        # обращение к OpenAI
       # client = OpenAI()        
        client = OpenAI(
            api_key="sk-or-vv-97eb792c85f0c225413a6e7ff5115b3629e227c0ff69ff32006b17960dc8e530", # ваш ключ в VseGPT после регистрации
            base_url="https://api.vsegpt.ru/v1",
        ) 

        response = client.chat.completions.create(
            model = 'gpt-4o-mini',
            messages = messages,
            temperature = 0
        )
        # получение ответа модели
        return response.choices[0].message.content    

    # МЕТОД: запрос к OpenAI
    #   system  - инструкция system
    #   user    - инструкция user
    #   model   - название модели
    #   temp    - температура 
    #   format  - формат ответа
    async def request(self, system, user, model = 'gpt-4o-mini', temp = None, format: dict = None):

        # подготовка параметров запроса
        client = AsyncOpenAI(
            api_key="sk-or-vv-97eb792c85f0c225413a6e7ff5115b3629e227c0ff69ff32006b17960dc8e530", # ваш ключ в VseGPT после регистрации
            base_url="https://api.vsegpt.ru/v1",
        )

        messages = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ]
                
        # запрос в OpenAI
        try:
        
            # выполнение запроса
            response = await client.chat.completions.create(
                model = model,
                messages = messages,
                temperature = temp,
                response_format = format
            )
            
            # проверка результата запроса
            if response.choices:
                return response.choices[0].message.content
            else:
                print('Не удалось получить ответ от модели.')
                raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail = 'Не удалось получить ответ от модели.')
        
        except Exception as e:
            # обработка ошибок и исключений
            print(f'Ошибка при запросе в OpenAI: {e}')
            raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail = f'Ошибка при запросе в OpenAI: {e}')        

    # МЕТОД: запрос к OpenAI асинхронный
    async def get_answer_async(self, query: str, select_db: str):
        
        if select_db == 'IAM':
            self.db = self.db_IAM
           
        else:
            self.db = self.db_ICM
        
        print(self.db)
        
        # получаем релевантные отрезки из базы знаний
        docs = self.db.similarity_search(query, k=6)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        
        # Добавляем историю диалога
        chat_history_text = '\n'.join(self.chat_history[-5:])
        print ('\n -------------------------------------------',chat_history_text, '\n -------------------------------------------',)
        # формируем инструкцию user
        user = f'''
            История диалога: {chat_history_text}
            Ответь на вопрос пользователя, но не упоминай данные тебе документы с информацией в ответе.
            Документ с информацией для ответа пользователю: {message_content}\n\n
            Вопрос пользователя: \n{query}
        '''

        # получение ответа модели        
        answer = await self.request(self.system, user, 'gpt-4o-mini', 0)
        
        # Сохраняем в историю
        self.chat_history.append(f'Пользователь: {query}')
        self.chat_history.append(f'Бот: {answer}')

        # возврат ответа
        return answer

    