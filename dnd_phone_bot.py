import logging
import csv
import requests
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import random
from telegram import Update
from telegram.ext import ContextTypes
import json
import aiohttp
from gtts import gTTS


# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы разговора
UPLOAD, STORY, PLAYER_ACTION = range(3)

# Хранение данных игроков
current_player_index = 0  # Индекс текущего игрока
players_data = []
playa = []
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
            c = Character(player_name, row[3], row[4], row[5], row[6], row[7], row[8])
            await update.message.reply_text(player_name)  #добавляем персонажа в очередь
            player_rolls[player_name] = 0  #присваиваем результаты бросков
    playa.append(c)
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
    await update.message.reply_text("Хотите начать игру или добавить еще персонажей? Скиньте файл если хотите добавить еще персонажей или напишите /start_game если хотите начать.")
    await show_order(update, context)


async def show_order(update: Update, context: ContextTypes.DEFAULT_TYPE): #показываем очередность ходов
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
        #апи ключ и формат в котором приходит ответ
        'Authorization': f'Bearer sk-M6nTKyYUrj_wB7u8VCZMAb4kP6ErJ0s8sxlh9Iu4xQT3BlbkFJ-MHp0LwkJT11Fbfteppyy2B3lRX4x9NfMD20bjT-cA',
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


def text_to_speech(text):
    tts = gTTS(text=text, lang='ru')
    tts.save("output.mp3")
    return "output.mp3"


async def generate_image(prompt):  #генерим пикчи по тексту от гпт
    headers = {
        'Authorization': f'Bearer "sk-M6nTKyYUrj_wB7u8VCZMAb4kP6ErJ0s8sxlh9Iu4xQT3BlbkFJ-MHp0LwkJT11Fbfteppyy2B3lRX4x9NfMD20bjT-cA',
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
    if context.user_data['message_format'] == 'text':
        await update.message.reply_text(story_start)
    else:
        audio_file_path = text_to_speech(story_start)
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_file_path, 'rb'))
    await update.message.reply_text("Игра началась! Введите ваши действия после команды /action.\nНапример так: '/action взять стакан'")


class Character:  #характеристки для проверки
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


def roll_d20():  #кубик
    return random.randint(1, 20)


async def perform_action(action: str, update: Update):  #ответ на действие героя
    character = playa[current_player_index]
    attribute = random.choice(list(character.attributes.keys()))  #выбираем рандом характеристику но по хорошему надо отдельно у гпт спрашивать какую характеристику данное действие использует
    threshold = random.randint(1, 20)  #также рандом но по хорошему через гпт
    roll = roll_d20()  #кидаем кубик
    success = roll + character.attributes[attribute] >= threshold  #проверяем если кубик + стата героя больше запрошенной

    #формируем запрос к GPT
    prompt = f"{character.name} выполняет действие: '{action}'. Результат броска: {roll}. " \
             f"Необходимая характеристика: {attribute}, Порог: {threshold}. " \
             f"Успех: {'да' if success else 'нет'}. Опиши, что происходит дальше."

    gpt_response = await ask_gpt(prompt)
    await update.message.reply_text(gpt_response)


# model = Model("path/to/vosk-model")  # Укажите путь к вашей модели


async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):   #эту хуету писала гпт вообще не факт что работает но расскажу как должна
    global current_player_index
    await show_order(update, context)
    action_text = ' '.join(context.args) if context.args else "действие"

    await perform_action(action_text, update) #обращаемся к функции которая дает нам необходимый результат и лстальную хуету

    current_player_index += 1 #переходим на следующего героя в очереди

    if current_player_index >= len(sorted_players): #если все герои походили
        current_player_index = 0  #сброс индекса для следующего раунда
        await continue_story(update)  #вызов функции продолжения истории
    else:
        next_character = playa[current_player_index]
        await update.message.reply_text(f"Теперь ход {next_character.name}. Введите ваше действие:")


async def continue_story(update: Update):  #после круга действий приходим сюда после чего снова идут дейсвтия
    #продолжения истории
    prompt = "Продолжи историю и подведи игроков к появлению врага."

    gpt_response = await ask_gpt(prompt)
    await update.message.reply_text(gpt_response)
    await show_order(update)
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
