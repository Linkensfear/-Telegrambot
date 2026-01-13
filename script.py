from multiprocessing.reduction import register

from telebot.handler_backends import State, StatesGroup
from telebot.custom_filters import StateFilter
import telebot
from gtts import gTTS
import os
import speech_recognition as sr
import requests
from pydub import AudioSegment

bot = telebot.TeleBot('')

from openai import OpenAI
client = OpenAI(api_key='')

vm = 0

class UserState(StatesGroup):
    waiting_reply_photo = State()


@bot.message_handler(commands=['start'])
def send_welcome(message):

    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, 'Привет! Я здесь чтобы тебя выслушать, чем хочешь поделиться?')

@bot.message_handler(commands=['clear'])
def clear(message):

    bot.delete_chat(message.chat.id)

@bot.message_handler(commands=['privacy'])
def send_privacy(message):

    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, 'Мы заботимся о вашей безопасности, поэтому бот не передаёт никакой информации третьим лицам. Все запросы идут напрямую на обработку искуственному интеллекту.Исходный код: https://github.com/Linkensfear/-Telegrambot')

@bot.message_handler(commands=['voice'])
def voice_mode(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global vm
    if vm == 1:
        vm = 0
        bot.send_message(message.chat.id, 'Теперь я буду отвечать текстовыми сообщениями.')
    else:
        vm = 1
        bot.send_message(message.chat.id, 'Теперь я буду отвечать голосовыми сообщениями.')

@bot.message_handler(commands=['test'])
def test_mode(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Сейчас я отправлю фото, постарайтесь описать, что вы видите на этой фотографии.")

    bot.send_photo(message.chat.id, "https://psyfactor.org/lib/i/rorschach_test_1.jpg")
    bot.register_next_step_handler(message, test_result)

def test_result(message):
    result = client.responses.create(
        model="gpt-4o-mini",
        instructions="Ты профессиональный психолог. Ты telegram чат-бот. Ты проводишь тест Роршаха, твоя задача проанализировать описание картинки и мнение пользователя и дать ответ в соответствии с описание фотографии. Описание фото: На этой картинке теста Роршаха только черные чернила. Карточка, с которой начинается эксперимент, подскажет, как пациент воспринимает новые и стрессовое задачи. Участники обычно видят в изображении летучую мышь, моль, бабочку или морду какого-то животного, подобного слону или кролику. Реакция на эту карточку дает общую характеристику человека. В конце сообщения напомни, что не стоит воспринимать резултат всерьёз, так как это пока что ранняя версия бота. Отвечай только на вопросы, связанные с психологией. Также можешь оказывать моральную поддержку пользователю.",
        input="Мнение пользователя" + message.text
    )

    if vm == 0:
        bot.send_message(message.chat.id, result.output_text)
    else:
        try:
            tts = gTTS(text=result.output_text, lang='ru')

            filename = f"voice_{message.id}.mp3"

            tts.save(filename)

            with open(filename, "rb") as voice_file:
                bot.send_voice(message.chat.id, voice_file)

            os.remove(filename)
        except Exception as e:
            print(e)

@bot.message_handler(content_types=['text'])
def text_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global vm

    response = client.responses.create(
        model="gpt-4o-mini",
        instructions="You are a professional psychologist.  Отвечай только на вопросы/рассуждения, связанные с психологией. Также можешь оказывать моральную поддержку пользователю.",
        input=message.text
    )

    if vm == 0:
        bot.send_message(message.chat.id, response.output_text)
    else:
        try:
            tts = gTTS(text=response.output_text, lang='ru')

            filename = f"voice_{message.id}.mp3"

            tts.save(filename)

            with open(filename, "rb") as voice_file:
                bot.send_voice(message.chat.id, voice_file)

            os.remove(filename)
        except Exception as e:
            print(e)

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
        print(e)
        print("Ошибка")
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
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service")
    except Exception as e:
        print(e)

@bot.message_handler(content_types=['voice'])
def voice_handler(message):
    global vm
    try:
        bot.send_chat_action(message.chat.id, 'typing')

        voice_file = download_voice_file(message.voice.file_id)

        if voice_file:
            text = speech_to_text(voice_file)

            response = response = client.responses.create(
                model="gpt-4o-mini",
                instructions="You are a professional psychologist.  Отвечай только на вопросы, связанные с психологией.",
                input=text
            )

            if vm == 0:
                bot.send_message(message.chat.id, response.output_text)
            else:
                try:
                    tts = gTTS(text=response.output_text, lang='ru')

                    filename = f"voice_{message.id}.mp3"

                    tts.save(filename)

                    with open(filename, "rb") as voice_file:
                        bot.send_voice(message.chat.id, voice_file)

                    os.remove(filename)
                except Exception as e:
                    print(e)
        else:
            bot.reply_to(message,"Неудалось обработать.")
    except Exception as e:
        print(e)









bot.polling(none_stop=True)
