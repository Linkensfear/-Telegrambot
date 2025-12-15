import telebot
from gtts import gTTS
import os
import speech_recognition as sr
import requests
from pydub import AudioSegment

bot = telebot.TeleBot('TelegramAPIToken')

from openai import OpenAI
client = OpenAI(api_key='Openaiapi_key')
vm = 0
@bot.message_handler(commands=['start'])



vm = 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, 'Привет! Я здесь чтобы тебя выслушать, чем хочешь поделиться?')

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

@bot.message_handler(content_types=['text'])
def text_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global vm

    response = client.responses.create(
        model="gpt-4o-mini",
        instructions="You are a professional psychologist. You are a chat-bot.",
        input=message.text
    )

    if vm == 0:
        bot.send_message(message.chat.id, response.text)
    else:
        try:
            tts = gTTS(text=response.text, lang='ru')

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
        print("Ошибка цйуйуцйуй")
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
                instructions="You are a professional psychologist.",
                input=text
            )

            if vm == 0:
                bot.send_message(message.chat.id, response.text)
            else:
                try:
                    tts = gTTS(text=response.text, lang='ru')

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
