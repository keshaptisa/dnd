import logging
import csv
import requests
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import random
from telegram import Update
from telegram.ext import ContextTypes
import json
import aiohttp
import openai
from gtts import gTTS
import os



# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы разговора
UPLOAD, STORY, PLAYER_ACTION = range(3)

# Хранение данных игроков
players_data = {}
player_rolls = {}
STORY_FILE = 'story.json'  # Файл для хранения истории


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Хотите получать сообщения в текстовом формате или в аудио? Напишите 'текст' или 'аудио'.")
    context.user_data['waiting_for_action'] = True  # Устанавливаем состояние ожидания

async def handle_message_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_action'):  # Проверяем состояние ожидания
        user_response = update.message.text.lower()

        if user_response == 'текст':
            context.user_data['message_format'] = 'text'
            await update.message.reply_text("Дорогие игроки! Добро пожаловать в наш волшебный мир приключений! Сегодня мы отправимся в захватывающее путешествие,/"
                                            " полное тайн, опасностей и невероятных открытий. Каждое ваше решение будет иметь значение, и каждый шаг может привести к неожиданным поворотам сюжета. Помните, что здесь нет неправильных решений — важно лишь ваше взаимодействие и творчество. Позвольте своим персонажам ожить, погружайтесь в их истории и не бойтесь рисковать!/"
                                            "Давайте создадим вместе незабываемую историю. Пусть удача всегда будет на вашей стороне, а ваши мечты — на грани реальности!Приготовьтесь к приключениям! Вперед, герои!")
            await update.message.reply_text('Этот бот лишь прототип, поэтому он включает не все функции реальной игры. Инструкция озвученная здесь является очень сжатой, вы можете ознакомиться с полной инструкцией по данной ссылке или же самостоятельно поискать информацию в своих гаджетах.')
            context.user_data['waiting_for_action'] = False  # Сбрасываем состояние ожидания
        elif user_response == 'аудио':
            context.user_data['message_format'] = 'audio'
            await update.message.reply_voice(voice=open('началодндмузыка.mp3', 'rb'))
            await update.message.reply_voice(voice=open('извинение.m4a', 'rb'))
            context.user_data['waiting_for_action'] = False  # Сбрасываем состояние ожидания
        else:
            await update.message.reply_text("Пожалуйста, ответьте 'текст' или 'аудио'.")
    await provide_instructions(update, context)


async def provide_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE): #инстркция текст
    instructions = (
        'Каждый игрок переходит в Telegram бот  для создания личности,выбирает имя, расу и остальные детали своего персонажа.  Как только игрок закончит, бот пришлет ему файл-анкету, ее нужно будет переслать сюда.   Игроки могут заходить в свой телеграмм бот чтобы вести учёт показателей, таких как уровень здоровья, количество денег и так далее, но это не обязательно.'
    )
    if context.user_data['message_format'] == 'text':
        await update.message.reply_text(instructions)
    else:
       #инструктаж в аудио формате
        await update.message.reply_voice(
            voice=open('инструктаж.m4a', 'rb'))
    #Ссылка на создание CSV файла
    await update.message.reply_text(
        "Чтобы создать героя, перейдите по следующей ссылке @dndphonehero_bot. Нажмите /continue чтобы продолжить")

#возвращение после создания анкеты
async def continue_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("С возвращением! Пожалуйста, перешли сюда книгу из таверны.")
    return UPLOAD

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file = await document.get_file()
    file_url = file.file_path
    file_path = f'./{document.file_name}'
    response = requests.get(file_url)
    with open(file_path, 'wb') as f:
        f.write(response.content)
    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            player_name = row[0]
            await update.message.reply_text(player_name)
            player_rolls[player_name] = 0  #присваиваем результаты бросков
    print(player_rolls)
    await update.message.reply_text("Данные успешно загружены! Используйте /roll для броска кубика.")

async def order_roll(update: Update, context: ContextTypes.DEFAULT_TYPE): #кубик
    player_name = None
    for k, v in player_rolls.items():
        if v == 0:
            player_name = k
    if player_name not in player_rolls:
        await update.message.reply_text("Вы не зарегистрированы в игре. Пожалуйста, загрузите книгу с данными.")
        return
    roll_result = random.randint(1, 20)  #бросок кубика к20
    player_rolls[player_name] = roll_result
    await update.message.reply_text(f"{player_name}, вы бросили кубик и получили: {roll_result}")
    # Запросить у пользователя, хочет ли он начать игру или добавить персонажей
    await update.message.reply_text("Хотите начать игру или добавить еще персонажей? Скиньте файл если хотите добавить еще персонажей или напишите /start_game если хотите начать'.")
    # Сохраняем состояние для обработки ответа
    #context.user_data['waiting_for_action'] = True
    await show_order(update, context)

#
# async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE): #для начала игры
#     if context.user_data.get('waiting_for_action'):
#         user_response = update.message.text.lower()
#         print(f"Received response: {user_response}")
#         if user_response == 'начать':
#             await show_order(update, context)
#             context.user_data['waiting_for_action'] = False  #сброс состояния
#         elif user_response == 'добавить':
#             await update.message.reply_text("Пожалуйста, добавьте персонажей.")
#         else:
#             await update.message.reply_text("Пожалуйста, ответьте 'начать' или 'добавить'.")

async def show_order(update: Update, context: ContextTypes.DEFAULT_TYPE): #показываем очередность ходов
    if not player_rolls:
        await update.message.reply_text("Нет зарегистрированных игроков.")
        return
    global sorted_players
    sorted_players = sorted(player_rolls.items(), key=lambda x: x[1], reverse=True)
    order_message = "Очередность участников:\n"
    for i, (player, roll) in enumerate(sorted_players, start=1):
        order_message += f"{i}. {player} - {roll}\n"
    await update.message.reply_text(order_message)



async def ask_gpt(prompt):
    headers = {
        'Authorization': f'Bearer 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',
        'Content-Type': 'application/json',
    }

    data = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': prompt}],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data['choices'][0]['message']['content']
            else:
                return f"Ошибка: {response.status}, {await response.text()}"


# from google-cloud import speech_v1p1beta1 as speech
#
# def transcribe_audio(audio_file):
#     client = speech.SpeechClient()
#
#     with open(audio_file, "rb") as audio:
#         content = audio.read()
#
#     audio = speech.RecognitionAudio(content=content)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=16000,
#         language_code="ru-RU",
#     )
#
#     response = client.recognize(config=config, audio=audio)
#
#     for result in response.results:
#         print("Transcript: {}".format(result.alternatives[0].transcript))
#         return result.alternatives[0].transcript

def text_to_speech(text):
    tts = gTTS(text=text, lang='ru')
    tts.save("output.mp3")
    os.system("start output.mp3")


#from google.cloud import texttospeech

# def text_to_speech(text):
#     client = texttospeech.TextToSpeechClient()
#
#     input_text = texttospeech.SynthesisInput(text=text)
#
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="ru-RU",
#         name="ru-RU-Wavenet-D"  # Выберите голос, который вам нравится
#     )
#
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MP3
#     )
#
#     response = client.synthesize_speech(
#         input=input_text, voice=voice, audio_config=audio_config
#     )
#
#     with open("output.mp3", "wb") as out:
#         out.write(response.audio_content)
#         print('Audio content written to file "output.mp3"')

# Не забудьте установить Google Cloud SDK и аутентифицироваться


async def generate_image(prompt):
    headers = {
        'Authorization': f'Bearer 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',
        'Content-Type': 'application/json',
    }

    data = {
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.openai.com/v1/images/generations', headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                image_url = response_data['data'][0]['url']
                return image_url
            else:
                return f"Ошибка: {response.status}, {await response.text()}"
async def start_game(update: Update, context: CallbackContext):
    prompt = "Создай начало истории для Dungeons & Dragons. Опиши где нахолятся герои и что вокруг них"
    story_start = await ask_gpt(prompt)

    # Сохранение начала истории в файл
    with open(STORY_FILE, 'w') as f:
        json.dump({"story": story_start}, f)
    text_to_speech(story_start)

    # Генерация изображения
    image_url = await generate_image(story_start)

    # Отправка изображения пользователю
    await update.message.reply_photo(photo=image_url)
    await update.message.reply_text(story_start)

    await update.message.reply_text(perform_action)


class Character:
    def __init__(self, name):
        self.name = name
        self.attributes = {
            'сила': random.randint(1, 20),
            'ловкость': random.randint(1, 20),
            'телесложение': random.randint(1, 20),
            'интеллект': random.randint(1, 20),
            'мудрость': random.randint(1, 20),
            'харизма': random.randint(1, 20)
        }


def roll_d20():
    return random.randint(1, 20)


async def perform_action(character: Character, action: str, update: Update):
    attribute = random.choice(list(character.attributes.keys()))
    threshold = random.randint(1, 20)

    roll = roll_d20()
    success = roll + character.attributes[attribute] >= threshold

    # Формируем запрос к GPT
    prompt = f"{character.name} выполняет действие: '{action}'. Результат броска: {roll}. " \
             f"Необходимая характеристика: {attribute}, Порог: {threshold}. " \
             f"Успех: {'да' if success else 'нет'}. Опиши, что происходит дальше."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    gpt_response = response['choices'][0]['message']['content']
    await update.message.reply_text(gpt_response)


async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index
    # if current_player_index >= len(sorted_players):
    #     await update.message.reply_text("Все игроки уже сделали свои действия. Игра завершена.")
    #     return

    character = sorted_players[current_player_index]
    action_text = ' '.join(context.args) if context.args else "действие"

    await perform_action(character, action_text, update)

    current_player_index += 1
    if current_player_index >= len(sorted_players):
        current_player_index = 0  # Сброс индекса для следующего раунда

def main():
    app = ApplicationBuilder().token("7243764957:AAG9YeIH9nKtxPUJR9oWOceyCV7RVShd5CU").build()
    app.add_handler(CommandHandler("start", start_bot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_format))
    app.add_handler(CommandHandler('continue', continue_bot))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CommandHandler("roll", order_roll))
    app.add_handler(CommandHandler("startgame", start_game))
    app.add_handler(CommandHandler("action", action))

    #app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))
    app.run_polling()

    # Добавьте обработчик команды /startgame
if __name__ == '__main__':
    main()