import logging
import csv
import base64
import httpx
import requests
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import random
from telegram import Update
from telegram.ext import ContextTypes
import json
import aiohttp
from gtts import gTTS
import wave
import json
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
import os


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD, STORY, PLAYER_ACTION = range(3)


current_player_index = 0
players_data = []
playa = []
player_rolls = {}
STORY_FILE = 'story.json'


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Хотите получать сообщения в текстовом формате или в аудио? Напишите 'текст' или 'аудио'.")
    context.user_data['waiting_for_action'] = True


async def handle_message_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_action'):
        user_response = update.message.text.lower()

        if user_response == 'текст':
            context.user_data['message_format'] = 'text'
            await update.message.reply_text("Дорогие игроки! Добро пожаловать в наш волшебный мир приключений! Сегодня мы отправимся в захватывающее путешествие,"
                                            " полное тайн, опасностей и невероятных открытий. Каждое ваше решение будет иметь значение, и каждый шаг может привести к неожиданным поворотам сюжета. Помните, что здесь нет неправильных решений — важно лишь ваше взаимодействие и творчество. Позвольте своим персонажам ожить, погружайтесь в их истории и не бойтесь рисковать!\n"
                                            "Давайте создадим вместе незабываемую историю. Пусть удача всегда будет на вашей стороне, а ваши мечты — на грани реальности! Приготовьтесь к приключениям! Вперед, герои!")
            await update.message.reply_text('Этот бот лишь прототип, поэтому он включает в себя не все функции реальной игры. Инструкция озвученная здесь является очень сжатой, вы можете ознакомиться с полной инструкцией по данной ссылке или же самостоятельно поискать информацию в своих гаджетах.')
            context.user_data['waiting_for_action'] = False
        elif user_response == 'аудио':
            context.user_data['message_format'] = 'audio'
            await update.message.reply_voice(voice=open('началодндмузыка.mp3', 'rb'))
            await update.message.reply_voice(voice=open('извинение.m4a', 'rb'))
            context.user_data['waiting_for_action'] = False
        else:
            await update.message.reply_text("Пожалуйста, ответьте 'текст' или 'аудио'.")
    await provide_instructions(update, context)


async def provide_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instructions = (
        'Каждый игрок переходит в Telegram бот для создания личности, выбирает имя, расу и остальные детали своего персонажа. Как только игрок закончит, бот пришлет ему файл-анкету, ее нужно будет переслать сюда. Игроки могут заходить в свой телеграмм бот чтобы вести учёт показателей, таких как уровень здоровья, количество денег и так далее, но это не обязательно.'
    )
    if context.user_data['message_format'] == 'text':
        await update.message.reply_text(instructions)
    else:
        await update.message.reply_voice(
            voice=open('инструктаж.m4a', 'rb'))
    await update.message.reply_text(
        "Чтобы создать героя, перейдите по следующей ссылке @dndphonehero_bot. Нажмите /continue чтобы продолжить")



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
            c = Character(player_name, row[3], row[4], row[5], row[6], row[7], row[8])
            await update.message.reply_text(player_name)
            player_rolls[player_name] = 0
    playa.append(c)
    await update.message.reply_text("Данные успешно загружены! Используйте /roll для броска кубика.")


async def order_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_name = None
    for k, v in player_rolls.items():
        if v == 0:
            player_name = k
    if player_name not in player_rolls:
        await update.message.reply_text("Вы не зарегистрированы в игре. Пожалуйста, загрузите книгу с данными.")
        return
    roll_result = random.randint(1, 20)
    player_rolls[player_name] = roll_result
    await update.message.reply_text(f"{player_name}, вы бросили кубик и получили: {roll_result}")
    await update.message.reply_text("Хотите начать игру или добавить еще персонажей? Скиньте файл если хотите добавить еще персонажей или напишите /start_game если хотите начать.")
    await show_order(update, context)


async def show_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not player_rolls:
        await update.message.reply_text("Нет зарегистрированных игроков.")
        return
    global sorted_players, playa
    sorted_players = sorted(player_rolls.items(), key=lambda x: x[1], reverse=True)
    pp = []
    for x in sorted_players:
        for ch in playa:
            if ch.name == x[0]:
                pp.append(ch)
    playa = pp.copy()

    order_message = "Очередность участников:\n"
    for i, (player, roll) in enumerate(sorted_players, start=1):
        order_message += f"{i}. {player} - {roll}\n"
    await update.message.reply_text(order_message)


async def ask_gpt(prompt):  #запрос в гпт
    headers = {
        'Authorization': f'Bearer sk-bWmuWR5oDsaP0ARLht6Z6MyhVqE9uDnxYJES3l24cyT3BlbkFJwymfBLJ-a0F3dfLHcoPGtpAQ_N_-1pIGBr3flwq4EA',
        'Content-Type': 'application/json',
    }

    data = {
        'model': 'gpt-4o-mini',
        'messages': [{'role': 'user', 'content': prompt}],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data['choices'][0]['message']['content']
            else:
                return f"Ошибка: {response.status}, {await response.text()}"


def text_to_speech(text):
    api_token = "a7c82240-4bff-4aad-917b-010e753d5e28"
    url = f"https://public.api.voice.steos.io/api/v1/synthesize-controller/synthesis-by-text?authToken={api_token}"

    body = {"voiceId": 1, "text": text, "pitchShift": 1.2, "speedMultiplier": 0.5, "format": "mp3"}

    response = httpx.post(url, json=body)
    answer = response.json()
    decoded_bytes = base64.b64decode(answer["fileContents"])

    with open("./output.mp3", "wb") as fout:
        fout.write(decoded_bytes)
    return "output.mp3"


async def generate_image(prompt):  # Генерируем изображения по тексту от GPT
    headers = {
        'Authorization': 'Bearer sk-bWmuWR5oDsaP0ARLht6Z6MyhVqE9uDnxYJES3l24cyT3BlbkFJwymfBLJ-a0F3dfLHcoPGtpAQ_N_-1pIGBr3flwq4EA',
        'Content-Type': 'application/json',
    }

    data = {
        'model': "dall-e-3",
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
                error_message = await response.text()
                return f"Ошибка: {response.status}, {error_message}"


async def start_game(update: Update, context: CallbackContext):
    prompt = "Создай начало истории для Dungeons & Dragons. Опиши где находятся герои и что вокруг них"
    story_start = await ask_gpt(prompt)

    global sorted_players, current_player_index
    current_player_index = 0

    with open(STORY_FILE, 'w') as f:
        json.dump({"story": story_start}, f)

    if context.user_data['message_format'] == 'text':
        await update.message.reply_text(story_start)
    else:
        audio_file_path = text_to_speech(story_start)
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_file_path, 'rb'))

    # Генерация изображения
    image_prompt = story_start  # Используем текст истории как подсказку для изображения
    image_url = await generate_image(image_prompt)

    # Отправка изображения пользователю
    if image_url.startswith("Ошибка"):
        await update.message.reply_text(image_url)  # Отправляем сообщение об ошибке
    else:
        await update.message.reply_photo(photo=image_url)

    # Отправка музыки после картинки
    if context.user_data['message_format'] == 'text':
        await update.message.reply_text("Теперь музыка!")
    else:
        audio_file_path = text_to_speech("Теперь музыка!")
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_file_path, 'rb'))

    await update.message.reply_text("Игра началась! Введите ваши действия после команды /action.\nНапример так: '/action взять стакан'")


class Character:
    def __init__(self, name, p1, p2, p3, p4, p5, p6):
        self.name = name
        self.attributes = {
            'сила': int(p1),
            'ловкость': int(p2),
            'телесложение': int(p3),
            'интеллект': int(p4),
            'мудрость': int(p5),
            'харизма': int(p6)
        }


async def roll_d20():  # кубик
    return random.randint(1, 20)


async def perform_action(action: str, update: Update):
    character = playa[current_player_index]  # Отправляем сообщение об ошибке
    attribute = random.choice(list(character.attributes.keys()))
    threshold = random.randint(1, 20)

    await update.message.reply_text(
        f"{character.name}, для проведения вашего действия необходимо подтвердить {attribute} {threshold}. Вы бросаете кубик!")
# как переделать эту хуйею
    roll = await roll_d20()  # Используем await для получения результата броска
    success = roll + character.attributes[attribute] >= threshold

    await update.message.reply_text(
        f"Результат броска: {roll}. Результат проверки: {(roll + character.attributes[attribute])}")

    prompt = (f"{character.name} выполняет действие: '{action}'. Результат броска: {roll}. "
              f"Необходимая характеристика: {attribute}, Порог: {threshold}. "
              f"Успех: {'да' if success else 'нет'}. Опиши, что происходит дальше.")

    gpt_response = await ask_gpt(prompt)
    await update.message.reply_text(gpt_response)
    image_prompt = gpt_response  # Используем текст истории как подсказку для изображения
    image_url = await generate_image(image_prompt)

    # Отправка изображения пользователю
    if image_url.startswith("Ошибка"):
        await update.message.reply_text(image_url)  # Отправляем сообщение об ошибке
    else:
        await update.message.reply_photo(photo=image_url)


def generate_music(prompt):
    url = "https://api.suno.ai/generate/music"  # URL API SunoAI для генерации музыки
    headers = {
        "Authorization": "Bearer YOUR_API_KEY",  # Замените на ваш API ключ
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "duration": 30,  # Длительность в секундах
        "genre": "classical"  # Укажите жанр, если это поддерживается
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        music_url = response.json().get("music_url")
        print(f"Сгенерированная музыка доступна по ссылке: {music_url}")
    else:
        print(f"Ошибка: {response.status_code} - {response.text}")
async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index
    await show_order(update, context)

    # Проверяем, есть ли аргументы
    if context.args:
        action_text = ' '.join(context.args)

        # Проверяем, является ли последний аргумент аудиофайлом
        if action_text.lower().endswith(('.mp3', '.wav', '.flac')):
            audio_file_path = action_text
            model_path = "vosk-model-small-ru-0.22"  # Укажите путь к вашей модели

            try:
                # Обработка аудиофайла
                text = transcribe_audio_to_text(audio_file_path, model_path)
                await perform_action(text, update)
                current_player_index += 1

                if current_player_index >= len(sorted_players):
                    current_player_index = 0
                    await continue_story(update)
                else:
                    next_character = playa[current_player_index]
                    await update.message.reply_text(f"Теперь ход {next_character.name}. Введите ваше действие:")
            except Exception as e:
                await update.message.reply_text(f"Ошибка при обработке аудио: {e}")
        else:
            # Если это текст, передаем его в perform_action
            await perform_action(action_text, update)
            current_player_index += 1

            if current_player_index >= len(sorted_players):
                current_player_index = 0
                await continue_story(update)
            else:
                next_character = playa[current_player_index]
                await update.message.reply_text(f"Теперь ход {next_character.name}. Введите ваше действие:")
    else:
        await perform_action("действие", update)  # Если нет аргументов, выполняем действие по умолчанию


def convert_to_wav(audio_file_path):
    # Конвертация аудиофайла в формат WAV
    audio = AudioSegment.from_file(audio_file_path)
    wav_file_path = "converted_audio.wav"
    audio.export(wav_file_path, format="wav")
    return wav_file_path


def transcribe_audio_to_text(audio_file_path, model_path):
    # Проверка существования модели
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")

    # Проверка существования аудиофайла
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found at {audio_file_path}")

    # Конвертация аудиофайла в WAV
    wav_file_path = convert_to_wav(audio_file_path)

    # Загрузка модели
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)

    # Открытие WAV-файла
    with wave.open(wav_file_path, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Audio file must be WAV format mono PCM.")

        # Чтение аудиоданных и распознавание речи
        transcript = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                transcript += json.loads(result)["text"] + " "
            else:
                recognizer.PartialResult()

        # Получение окончательного результата
        final_result = recognizer.FinalResult()
        transcript += json.loads(final_result)["text"]

    return transcript.strip()

async def continue_story(update: Update):
    prompt = "Продолжи историю и подведи игроков к появлению врага."

    gpt_response = await ask_gpt(prompt)
    await update.message.reply_text(gpt_response)
    await show_order(update)
    await action(update)


def main():
    app = ApplicationBuilder().token("7243764957:AAG9YeIH9nKtxPUJR9oWOceyCV7RVShd5CU").build()

    app.add_handler(CommandHandler("start", start_bot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_format))
    app.add_handler(CommandHandler('continue', continue_bot))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CommandHandler("roll", order_roll))
    app.add_handler(CommandHandler("start_game", start_game))
    app.add_handler(CommandHandler("action", action))

    app.run_polling()


if __name__ == '__main__':
    main()
