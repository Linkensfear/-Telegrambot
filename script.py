import json
from telebot import types
import traceback
import telebot
from gtts import gTTS
import os
import speech_recognition as sr
import requests
from pydub import AudioSegment
import logging
import time
from openai import OpenAI




bot = telebot.TeleBot('BOTTOKEN')
client = OpenAI(api_key='APIKEY')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AUTH_FILE = 'authorized_users.txt'
VOICE_MODE_FILE = 'voice_mode_users.txt'
PASSWORD = '322322'
# Удаляем вебхук, если он был
bot.remove_webhook()
time.sleep(0.5)

def is_voice_mode(user_id):

    if not os.path.exists(VOICE_MODE_FILE):
        return False
        
    with open(VOICE_MODE_FILE, 'r') as f:
        
        for line in f:
            line = line.strip()
            
            if line and int(line) == user_id:
                return True
    return False

def set_voice_mode(user_id, on):

    users = []

    if os.path.exists(VOICE_MODE_FILE):
        with open(VOICE_MODE_FILE, 'r') as f:

            for line in f:
                line = line.strip()

                if line:
                    uid = int(line)
                    if uid != user_id:
                        users.append(uid)
                        
    if on:
        users.append(user_id)

    with open(VOICE_MODE_FILE, 'w') as f:
        for uid in users:
            f.write(f"{uid}\n")

def create_response(instructions, message, user_id):
    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=message,
            store=True,
            instructions=instructions,

            conversation=authorized_users[str(user_id)])
        return response.output_text
    except Exception as e:
        logger.error(e)
        return "Ошибка нейросети."
    #response = f"(Ответ нейросети) ({message}) ({instructions})"
    client.responses.create()

authorized_users = {}

def load_users():
    global authorized_users
    try:
        with open(AUTH_FILE, 'r') as f:
            authorized_users = json.load(f)
    except:
        authorized_users = {}

def save_users():
    global authorized_users
    with open(AUTH_FILE, 'w') as f:
        json.dump(authorized_users, f)

def is_authorized(user_id):
    return str(user_id) in authorized_users
'''
def is_authorized(user_id):
    """
    Проверяет, есть ли user_id в файле авторизованных пользователей.
    Возвращает True, если пользователь авторизован, иначе False.
    """
    if not os.path.exists(AUTH_FILE):
        return False
    with open(AUTH_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and int(line) == user_id:
                return True
    return False
'''

def authorize_user(user_id):

    #with open(AUTH_FILE, 'a') as f:
    #    f.write(f"{user_id}\n")
    conv = client.conversations.create()
    authorized_users[str(user_id)] = conv.id
    save_users()

load_users()

questions = [
    # E/I
    ("1. На вечеринке вы:",
     "A. Общаетесь со многими, включая незнакомцев",
     "B. Общаетесь с несколькими знакомыми", "EI"),
    ("2. Вы скорее:",
     "A. Человек общительный",
     "B. Человек сдержанный", "EI"),
    ("3. Вы предпочитаете:",
     "A. Работать в группе",
     "B. Работать самостоятельно", "EI"),
    ("4. В свободное время вы:",
     "A. Идете к людям",
     "B. Остаетесь дома", "EI"),
    ("5. Новые знакомства:",
     "A. Заряжают вас энергией",
     "B. Тратят вашу энергию", "EI"),

    # S/N
    ("6. Вы больше доверяете:",
     "A. Фактам и деталям",
     "B. Идеям и концепциям", "SN"),
    ("7. Вам интереснее:",
     "A. То, что реально и ощутимо",
     "B. То, что возможно и воображаемо", "SN"),
    ("8. При обучении вы предпочитаете:",
     "A. Конкретные инструкции",
     "B. Общие принципы", "SN"),
    ("9. Вы чаще замечаете:",
     "A. То, что происходит здесь и сейчас",
     "B. То, что может произойти в будущем", "SN"),
    ("10. Вас больше привлекают:",
     "A. Практические задачи",
     "B. Теоретические задачи", "SN"),

    # T/F
    ("11. При принятии решений вы опираетесь на:",
     "A. Логику и объективность",
     "B. Личные ценности и чувства", "TF"),
    ("12. Вас чаще можно назвать:",
     "A. Справедливым и принципиальным",
     "B. Сострадательным и мягким", "TF"),
    ("13. Вам важнее:",
     "A. Истина",
     "B. Гармония", "TF"),
    ("14. Вы скорее похвалите человека за:",
     "A. Правильное решение",
     "B. Доброе отношение", "TF"),
    ("15. Конфликты вы склонны:",
     "A. Анализировать и искать причину",
     "B. Сглаживать и учитывать чувства", "TF"),

    # J/P
    ("16. Вы предпочитаете:",
     "A. Планировать и организовывать",
     "B. Импровизировать и быть гибким", "JP"),
    ("17. Вам комфортнее, когда:",
     "A. Есть четкий план",
     "B. Есть свобода выбора", "JP"),
    ("18. Вы чаще:",
     "A. Заканчиваете дела вовремя",
     "B. Откладываете дела на потом", "JP"),
    ("19. Порядок на рабочем месте:",
     "A. Важен для вас",
     "B. Не имеет значения", "JP"),
    ("20. Вы предпочитаете:",
     "A. Четкие сроки и график",
     "B. Открытые возможности", "JP"),
]

# Описания типов
descriptions = {
    "ISTJ": "Логистик — организованный, практичный, ответственный.",
    "ISFJ": "Защитник — добросовестный, заботливый, преданный.",
    "INFJ": "Активист — идеалистичный, принципиальный, проницательный.",
    "INTJ": "Стратег — независимый, аналитичный, целеустремлённый.",
    "ISTP": "Виртуоз — гибкий, наблюдательный, практичный.",
    "ISFP": "Посредник — чуткий, художественный, гармоничный.",
    "INFP": "Целитель — идеалистичный, преданный, творческий.",
    "INTP": "Мыслитель — изобретательный, логичный, теоретичный.",
    "ESTP": "Делец — энергичный, рациональный, общительный.",
    "ESFP": "Развлекатель — спонтанный, жизнерадостный, артистичный.",
    "ENFP": "Борец — энтузиаст, креативный, общительный.",
    "ENTP": "Полемист — изобретательный, любознательный, спорщик.",
    "ESTJ": "Менеджер — практичный, организованный, лидер.",
    "ESFJ": "Консул — заботливый, социальный, добросовестный.",
    "ENFJ": "Тренер — харизматичный, вдохновляющий, альтруистичный.",
    "ENTJ": "Командир — решительный, стратегический, амбициозный."
}

user_data = {}

def get_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_a = types.InlineKeyboardButton("A", callback_data="A")
    btn_b = types.InlineKeyboardButton("B", callback_data="B")
    keyboard.add(btn_a, btn_b)
    return keyboard

def send_question(chat_id, q_index):
    if q_index >= len(questions):
        return
    q_text, opt_a, opt_b, _ = questions[q_index]
    message_text = f"{q_text}\n\n{opt_a}\n{opt_b}"
    bot.send_message(chat_id, message_text, reply_markup=get_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    # Сразу отвечаем на callback, чтобы убрать "часики" на кнопке
    bot.answer_callback_query(call.id)

    # Проверяем, есть ли данные пользователя
    if user_id not in user_data:
        bot.send_message(user_id, "Пожалуйста, начните тест заново с помощью /mbti")
        return

    data = user_data[user_id]
    q_index = data['q_index']

    # Если тест завершён
    if q_index >= len(questions):
        bot.send_message(user_id, "Тест уже завершён. Начните новый с помощью /mbti")
        return

    # Получаем шкалу текущего вопроса
    _, _, _, scale = questions[q_index]
    answer = call.data

    # Обновляем счётчики
    if scale == "EI":
        if answer == 'A':
            data['scores']['E'] += 1
        else:
            data['scores']['I'] += 1
    elif scale == "SN":
        if answer == 'A':
            data['scores']['S'] += 1
        else:
            data['scores']['N'] += 1
    elif scale == "TF":
        if answer == 'A':
            data['scores']['T'] += 1
        else:
            data['scores']['F'] += 1
    elif scale == "JP":
        if answer == 'A':
            data['scores']['J'] += 1
        else:
            data['scores']['P'] += 1

    # Пытаемся убрать клавиатуру у сообщения с вопросом
    try:
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    except Exception as e:
        logger.error(f"Ошибка при удалении клавиатуры: {e}")
        traceback.print_exc()


    data['q_index'] += 1
    new_index = data['q_index']

    if new_index < len(questions):
        send_question(user_id, new_index)
    else:
        scores = data['scores']
        type_ei = 'E' if scores['E'] >= scores['I'] else 'I'
        type_sn = 'S' if scores['S'] >= scores['N'] else 'N'
        type_tf = 'T' if scores['T'] >= scores['F'] else 'F'
        type_jp = 'J' if scores['J'] >= scores['P'] else 'P'
        mbti_type = type_ei + type_sn + type_tf + type_jp

        result_text = (
            f"📊 **Результаты теста**\n\n"
            f"E: {scores['E']}  I: {scores['I']}  →  {type_ei}\n"
            f"S: {scores['S']}  N: {scores['N']}  →  {type_sn}\n"
            f"T: {scores['T']}  F: {scores['F']}  →  {type_tf}\n"
            f"J: {scores['J']}  P: {scores['P']}  →  {type_jp}\n\n"
            f"**Ваш тип личности по MBTI:** {mbti_type}\n\n"
            f"_{descriptions.get(mbti_type, 'Описание временно отсутствует.')}_"
            'Оригинальный сайт: https://www.16personalities.com'
        )
        bot.send_message(user_id, result_text, parse_mode='Markdown')

        del user_data[user_id]


@bot.message_handler(commands=['mbti'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {
        'q_index': 0,
        'scores': {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
    }
    bot.send_message(
        user_id,
        "🧠 Добро пожаловать в MBTI тест!\n"
        "Вам будет предложено 20 вопросов с двумя вариантами ответа.\n"
        "Нажимайте кнопки A или B для выбора.\n"
        "Начнём!"
    )
    send_question(user_id, 0)

@bot.message_handler(commands=['start'])
def send_welcome(message):

    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, 'Приветствую! Для доступа к режиму ИИ введите пароль.')


@bot.message_handler(commands=['privacy'])
def send_privacy(message):

    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, 'Мы заботимся о вашей безопасности, поэтому бот не передаёт никакой информации третьим лицам. Все запросы идут напрямую на обработку искуственному интеллекту.Исходный код: https://github.com/Linkensfear/-Telegrambot')

@bot.message_handler(commands=['voice'])
def voice_mode(message):
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    # Переключаем режим
    current_mode = is_voice_mode(user_id)
    new_mode = not current_mode
    set_voice_mode(user_id, new_mode)

    status = "включён" if new_mode else "выключен"
    bot.reply_to(message, f"Режим голосовых сообщений {status}.")


@bot.message_handler(commands=['test'])
def test_handler(message):
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Сейчас я отправлю фото, постарайтесь описать, что вы видите на этой фотографии.")

    bot.send_photo(message.chat.id, "https://psyfactor.org/lib/i/rorschach_test_1.jpg")

    if is_authorized(user_id):
        bot.register_next_step_handler(message, test_result)
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, 'Режим ИИ недоступен, введите пароль или используйте другую команду.')

def test_result(message):
    response = create_response('Тест', message.text, message.from_user.id)

    if is_voice_mode(message.from_user.id):
        send_text_to_speech(response, message)
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, response)


@bot.message_handler(content_types=['text'])
def text_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_id = message.from_user.id
    text = message.text

    if text == PASSWORD:
        if is_authorized(user_id):
            bot.reply_to(message, "Вы уже авторизованы.")
        else:
            authorize_user(user_id)
            bot.reply_to(message, "Пароль верный! Теперь вам доступен режим ИИ.")
    else:
        if is_authorized(user_id):
            response = create_response(
                #'',
                'Ты телеграм чат-бот психолог, твоя задача отвечать на сообщения пользователя как профессиональный психоаналитик и давать советы. Не отвечай на вопросы и сообщения не связанные с психологией.',
                text,
                user_id)
            if is_voice_mode(user_id):
                send_text_to_speech(response, message)
            else:
                bot.send_chat_action(message.chat.id, 'typing')
                bot.send_message(message.chat.id, response)
        else:
            bot.send_chat_action(message.chat.id, 'typing')
            bot.send_message(message.chat.id, 'Пароль неверный. Режим ИИ недоступен, попробуйте ещё раз или введите другую команду.')



def send_text_to_speech(response, message):
    tts = gTTS(text=response, lang='ru')

    filename = f"voice_{message.id}.mp3"

    tts.save(filename)

    with open(filename, "rb") as voice_file:
        bot.send_voice(message.chat.id, voice_file)

    os.remove(filename)

def download_voice_file(file_id):
    try:
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

        reply = requests.get(file_url)
        ogg_filename = f"voice_{file_id}.ogg"
        with open(ogg_filename, "wb") as f:
            f.write(reply.content)
            f.close()

        wav_filename = f"voice_{file_id}.wav"
        audio = AudioSegment.from_ogg(ogg_filename)

        audio.export(wav_filename, format="wav")
        os.remove(ogg_filename)

        return wav_filename
    except Exception as e:
        logger.error(e)
        logger.error("Ошибка")
        return None

def speech_to_text(audio_file):
    try:
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)

            text = recognizer.recognize_google(
                audio_data,
                language='ru-RU'
            )

            return text
    except sr.UnknownValueError:
        logger.error("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        logger.error("Could not request results from Google Speech Recognition service")
    except Exception as e:
        logger.error(e)

@bot.message_handler(content_types=['voice'])
def voice_handler(message):
    user_id = message.from_user.id
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        voice_file = download_voice_file(message.voice.file_id)

        if voice_file:
            text = speech_to_text(voice_file)
            os.remove(voice_file)

            if is_authorized(user_id):
                response = create_response(
                    'Ты телеграм чат-бот психолог, твоя задача отвечать на сообщения пользователя как профессиональный психоаналитик и давать советы. Не отвечай на вопросы и сообщения не связанные с психологией.',
                    text,
                    user_id)
                if is_voice_mode(user_id):
                    send_text_to_speech(response, message)
                else:
                    bot.send_chat_action(message.chat.id, 'typing')
                    bot.send_message(message.chat.id, response)
            else:
                bot.send_chat_action(message.chat.id, 'typing')
                bot.send_message(message.chat.id, 'Режим ИИ недоступен, введите пароль или используйте другую команду.')
        else:
            bot.reply_to(message,"Неудалось обработать.")
    except Exception as e:
        logger.error(e)




if __name__ == '__main__':
    logger.info("Бот запущен...")

    bot.infinity_polling()
