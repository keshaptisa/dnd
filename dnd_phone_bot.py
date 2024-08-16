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
import asyncio
import wave
from vosk import Model, KaldiRecognizer


# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы разговора
UPLOAD, STORY, PLAYER_ACTION = range(3)

# Хранение данных игроков
current_player_index = 0  # Индекс текущего игрока
players_data = {}
player_rolls = {}
STORY_FILE = 'story.json'  # Файл для хранения истории


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE): #запуск бота
    await update.message.reply_text(
        "Хотите получать сообщения в текстовом формате или в аудио? Напишите 'текст' или 'аудио'.")
    context.user_data['waiting_for_action'] = True  # Устанавливаем состояние ожидания


async def handle_message_format(update: Update, context: ContextTypes.DEFAULT_TYPE):  #приветсвие и узнаем текст или аудио ввод
    if context.user_data.get('waiting_for_action'):  # Проверяем состояние ожидания
        user_response = update.message.text.lower()

        if user_response == 'текст':
            context.user_data['message_format'] = 'text'
            await update.message.reply_text("Дорогие игроки! Добро пожаловать в наш волшебный мир приключений! Сегодня мы отправимся в захватывающее путешествие,"
                                            " полное тайн, опасностей и невероятных открытий. Каждое ваше решение будет иметь значение, и каждый шаг может привести к неожиданным поворотам сюжета. Помните, что здесь нет неправильных решений — важно лишь ваше взаимодействие и творчество. Позвольте своим персонажам ожить, погружайтесь в их истории и не бойтесь рисковать!\n"
                                            "Давайте создадим вместе незабываемую историю. Пусть удача всегда будет на вашей стороне, а ваши мечты — на грани реальности! Приготовьтесь к приключениям! Вперед, герои!")
            await update.message.reply_text('Этот бот лишь прототип, поэтому он включает в себя не все функции реальной игры. Инструкция озвученная здесь является очень сжатой, вы можете ознакомиться с полной инструкцией по данной ссылке или же самостоятельно поискать информацию в своих гаджетах.')
            context.user_data['waiting_for_action'] = False  # Сбрасываем состояние ожидания
        elif user_response == 'аудио':
            context.user_data['message_format'] = 'audio'
            await update.message.reply_voice(voice=open('началодндмузыка.mp3', 'rb'))
            await update.message.reply_voice(voice=open('извинение.m4a', 'rb'))
            context.user_data['waiting_for_action'] = False  # Сбрасываем состояние ожидания
        else:
            await update.message.reply_text("Пожалуйста, ответьте 'текст' или 'аудио'.")
    await provide_instructions(update, context)


async def provide_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE): #инстркция
    instructions = (
        'Каждый игрок переходит в Telegram бот для создания личности, выбирает имя, расу и остальные детали своего персонажа. Как только игрок закончит, бот пришлет ему файл-анкету, ее нужно будет переслать сюда. Игроки могут заходить в свой телеграмм бот чтобы вести учёт показателей, таких как уровень здоровья, количество денег и так далее, но это не обязательно.'
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


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):  #получаем файл с инфой про перса и обрабатываем его
    document = update.message.document
    file = await document.get_file()
    file_url = file.file_path
    file_path = f'./{document.file_name}'
    response = requests.get(file_url)
    with open(file_path, 'wb') as f:
        f.write(response.content)
    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, delimiter=',') #если файл считывает не только имя поменяй delimiter на ',' или ';'
        for row in reader:
            player_name = row[0]  #первый столбец имя
            await update.message.reply_text(player_name)  #добавляем персонажа в очередь
            player_rolls[player_name] = 0  #присваиваем результаты бросков
    print(player_rolls)
    await update.message.reply_text("Данные успешно загружены! Используйте /roll для броска кубика.")


async def order_roll(update: Update, context: ContextTypes.DEFAULT_TYPE): #кубик
    player_name = None
    for k, v in player_rolls.items():
        if v == 0:
            player_name = k  #ищем кто не кидал кубик то есть новый герой в очереди
    if player_name not in player_rolls:
        await update.message.reply_text("Вы не зарегистрированы в игре. Пожалуйста, загрузите книгу с данными.")
        return
    roll_result = random.randint(1, 20)  #бросок кубика к20
    player_rolls[player_name] = roll_result  #присваиваем результат
    await update.message.reply_text(f"{player_name}, вы бросили кубик и получили: {roll_result}")
    #спросить у пользователя хочет ли он начать игру или добавить персонажей
    await update.message.reply_text("Хотите начать игру или добавить еще персонажей? Скиньте файл если хотите добавить еще персонажей или напишите /start_game если хотите начать'.")
    await show_order(update, context)


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


async def ask_gpt(prompt):  #запрос в гпт
    headers = {
        #апи ключ и формат в котором приходит ответ
        'Authorization': f'Bearer sk-EEbaLASG4MCcyhXgkHFkfUSwt96qN2QWMybGbyDxHbT3BlbkFJv6XUPYAFTmmemvc3qYxXZTB08a32ItgLERPbhyWeEA',
        'Content-Type': 'application/json',
    }

    data = {
        #модель гпт можно менять
        'model': 'gpt-4o-mini',
        'messages': [{'role': 'user', 'content': prompt}],  #чтобы использовать надо отправить промт
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data['choices'][0]['message']['content'] #выводим ответ гпт
            else:
                return f"Ошибка: {response.status}, {await response.text()}"  #скорее всего не включен впн


def text_to_speech(text):  #озвучка текста от гпт но нема выбора голоса
    tts = gTTS(text=text, lang='ru')
    tts.save("output.mp3")
    os.system("start output.mp3")
# в этой есть нужный но хз работает или нет
#
# response = openai.ChatCompletion.create(
#     model="tts-1",
#     voice="Onyx",
#     input=response['choices'][0]['message']['content'],
# )
#
# response.stream_to_file("output.mp3")


async def generate_image(prompt):  #генерим пикчи по тексту от гпт
    headers = {
        'Authorization': f'Bearer "sk-EEbaLASG4MCcyhXgkHFkfUSwt96qN2QWMybGbyDxHbT3BlbkFJv6XUPYAFTmmemvc3qYxXZTB08a32ItgLERPbhyWeEA',
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

async def start_game(update: Update, context: CallbackContext):  #начало игры
    prompt = "Создай начало истории для Dungeons & Dragons. Опиши где находятся герои и что вокруг них"
    story_start = await ask_gpt(prompt)
    global sorted_players, current_player_index
    current_player_index = 0  # Сброс индекса игроков
    with open(STORY_FILE, 'w') as f:
        json.dump({"story": story_start}, f)

    #генерация аудио и изображения параллельно
    audio_task = asyncio.create_task(text_to_speech(story_start))
    image_task = asyncio.create_task(generate_image(story_start))

    #ожидание завершения задач
    audio_file_path = await audio_task
    image_url = await image_task

    #отправка изображения и аудио пользователю
    await update.message.reply_photo(photo=image_url)
    if context.user_data['message_format'] == 'text':
        await update.message.reply_text(story_start)
    else:
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_file_path, 'rb'))
    await update.message.reply_text("Игра началась! Введите ваши действия с помощью команды /action.")


class Character:  #характеристки для проверки
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


def roll_d20():  #кубик
    return random.randint(1, 20)


async def perform_action(character: Character, action: str, update: Update):  #ответ на действие героя
    attribute = random.choice(list(character.attributes.keys()))  #выбираем рандом характеристику но по хорошему надо отдельно у гпт спрашивать какую характеристику данное действие использует
    threshold = random.randint(1, 20)  #также рандом но по хорошему через гпт
    roll = roll_d20()  #кидаем кубик
    success = roll + character.attributes[attribute] >= threshold  #проверяем если кубик + стата героя больше запрошенной

    #формируем запрос к GPT
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


# model = Model("path/to/vosk-model")  # Укажите путь к вашей модели


async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):   #эту хуету писала гпт вообще не факт что работает но расскажу как должна
    global current_player_index

    character = sorted_players[current_player_index] #с нулевого пользователя идем по списку с очередность героев

    if update.message.text: #тут смотрим ответ по действию пришел в тексе или гс
        # Обработка текстового сообщения
        action_text = ' '.join(context.args) if context.args else "действие"
    elif update.message.audio:
        # Обработка аудио сообщения
        audio_file = await context.bot.get_file(update.message.audio.file_id)
        audio_path = f"{audio_file.file_id}.ogg"  #сохранение файла
        await audio_file.download(audio_path)

        #конвертация OGG в WAV (если необходимо)
        os.system(f"ffmpeg -i {audio_path} {audio_path.replace('.ogg', '.wav')}")

        #распознавание речи из аудио
        wf = wave.open(audio_path.replace('.ogg', '.wav'), "rb")
        rec = KaldiRecognizer(model, wf.getframerate())

        action_text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                action_text = rec.Result()
            else:
                rec.PartialResult()
                #если эта хуйня не работает то вот еще вариант но надо ввести путь и куда потом этот текст
                # from openai import OpenAI
                # client = OpenAI()
                #
                # audio_file = open("/path/to/file/audio.mp3", "rb")
                # transcription = client.audio.transcriptions.create(
                #     model="whisper-1",
                #     file=audio_file
                # )
                # print(transcription.text)
        action_text = json.loads(action_text).get('text', "Не удалось распознать аудио.")

    await perform_action(character, action_text, update) #обращаемся к функции которая дает нам необходимый результат и лстальную хуету

    current_player_index += 1 #переходим на следующего героя в очереди

    if current_player_index >= len(sorted_players): #если все герои походили
        current_player_index = 0  #сброс индекса для следующего раунда
        await continue_story(update)  #вызов функции продолжения истории
    else:
        next_character = sorted_players[current_player_index]
        await update.message.reply_text(f"Теперь ход {next_character.name}. Введите ваше действие или отправьте аудио:")


async def continue_story(update: Update):  #после круга действий приходим сюда после чего снова идут дейсвтия
    #продолжения истории
    prompt = "Продолжи историю и подведи игроков к появлению врага."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    gpt_response = response['choices'][0]['message']['content']
    await update.message.reply_text(gpt_response)
    await action(update)  #вызов функции приема дейсвий


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
