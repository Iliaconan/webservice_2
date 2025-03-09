# импорт библиотек
from fastapi import FastAPI                         # библиотека FastAPI
from pydantic import BaseModel                      # модуль для объявления структуры данных
from api.chunks import Chunk                        # модуль для работы с OpenAI
from fastapi.middleware.cors import CORSMiddleware  # класс для работы с CORS
from fastapi.responses import JSONResponse

# создаем объект приложения FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# создадим объект для работы с OpenAI
chunk = Chunk()

# класс с типами данных параметров 
class Item(BaseModel):
    name: str
    description: str
    old: int
    
# класс параметров калькулятора
class ModelCalc(BaseModel):
    a: float
    b: float        

# класс параметров распознавания изображения
class ModelOcr(BaseModel):
    image: str
    text: str

# класс с типами данных для метода api/get_answer
class ModelAnswer(BaseModel):
    text: str   
    select_db: str 
    
# класс параметров запроса к openai
class ModelRequest(BaseModel):
    system: str = ''
    user: str = ''
    temperature: float = 0.5
    format: dict = None

# функция, которая будет обрабатывать запрос по пути "/"
# полный путь запроса http://127.0.0.1:8000/
@app.get("/")
def root(): 
    return {"message": "Hello FastAPI"}

# функция, которая обрабатывает запрос по пути "/about"
@app.get("/about")
def about():
    return {"message": "Страница с описанием проекта"}

# функция-обработчик с параметрами пути
@app.get("/users/{id}")
def users(id):
    return {"Вы ввели user_id": id}  

# функция-обработчик post запроса с параметрами
@app.post('/users')
def post_users(item: Item):
    return {'answer': f'Пользователь {item.name} - {item.description}, возраст {item.old} лет'}  

# функция-обработчик post запроса с параметрами
@app.post('/add')
def post_add(item:ModelCalc):
    result = item.a + item.b
    return {'result': result}

# функция обработки post запроса + декоратор 
@app.post('/api/get_answer')
def get_answer(question: ModelAnswer):
    answer = chunk.get_answer(query = question.text, select_db = question.select_db)
    return {'message': answer}    

# функция обработки post запроса + декоратор  (асинхронная)
@app.post('/api/get_answer_async')
async def get_answer_async(question: ModelAnswer):
    answer = await chunk.get_answer_async(query = question.text, select_db = question.select_db)
    return {'message': answer}     

# функция распознавания изображения
@app.post('/api/image_ocr')
async def post_ocr(question: ModelOcr):
    answer = await chunk.ocr_image({
        'image': question.image,
        'text': question.text
    })
    return {'message': answer} 

# функция обращения к openai
@app.post('/api/request')
async def post_request(question: ModelRequest):
    answer = await chunk.request(
        system = question.system,
        user = question.user,
        temp = question.temperature,
        format = question.format
    )
    return {'message': answer} 

