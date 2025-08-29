import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import requests
from bs4 import BeautifulSoup
import json

# Клавиатура для взаимодействия с пользователем.
def create_keyboard(buttons):
    keyboard = VkKeyboard(one_time=False)
    for i, button in enumerate(buttons):
        if i > 0 and i % 2 == 0:
            keyboard.add_line()
        keyboard.add_button(button['label'], color=button['color'])
    return keyboard.get_keyboard()

# Функция, сокращающая текст до 40 символов (Ограничение).
def shorten_text(text, max_length=40):
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text

# Функция, выводящая список доступных курсов.
def get_vk_courses():
    try:
        # Парсим страницу с помощью requests и BeautifulSoup.
        url = "https://education.vk.company/students"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            return ["Не удалось найти данные о курсах."]
        # Получаем данные со страницы в формате json и обрабатываем.
        data = json.loads(script_tag.string)
        courses = data.get("props", {}).get("pageProps", {}).get("page", {}).get("programs", [])

        result = []
        for course in courses:
            # Проверяем, что курс открыт.
            if course.get("selection_status") == "open":
                name = course.get("name", "Название не указано")
                description = course.get("description", "Описание отсутствует")
                format_ = course.get("format", "Формат не указан")
                result.append(f"📌 {name}\n{description}\nФормат: {format_}\n")

        return result if result else ["В данный момент нет доступных курсов."]
    except Exception as e:
        return [f"Error with courses: {str(e)}"]


# Функция для получения вопросов и ответов.
def get_faq_data():
    try:
        # Аналогичный парсинг частых вопросов и ответов с сайта.
        url = "https://education.vk.company/students"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            return False

        data = json.loads(script_tag.string)
        questions = data.get("props", {}).get("pageProps", {}).get("page", {}).get("questions", [])

        # Создаем меню FAQ
        menu = []
        answers = {}

        for q in questions:
            question_text = q['question']
            short_question = shorten_text(question_text)
            menu.append({'label': short_question, 'color': VkKeyboardColor.SECONDARY})
            answers[short_question] = f"❓ Вопрос: {question_text}\n\n{q['answer']}"

        menu.append({'label': 'Назад', 'color': VkKeyboardColor.NEGATIVE})

        return menu, answers
    except Exception as e:
        print(f"Error with FAQ: {str(e)}")
        return None, None

# Функция для получения проектов со страницы VK Education Projects.
def get_projects():
    try:
        # URL API с проектами.
        api_url = "https://store.tildaapi.com/api/getproductslist/?storepartuid=357127554781&recid=754421136&getparts=true&getoptions=true&slice=1&sort[created]=desc&size=9"

        # GET.
        response = requests.get(api_url)
        response.raise_for_status()

        # Парсим ответ в виде JSON.
        data = response.json()
        projects = data.get('products', [])

        # Обрабатываем проекты.
        formatted_projects = []
        for project in projects:
            title = project.get('title', 'Без названия')
            direction = next(
                (ch['value'] for ch in project.get('characteristics', [])
                 if ch.get('title') == 'Направление'),
                'Не указано'
            )
            duration = next(
                (ch['value'] for ch in project.get('characteristics', [])
                 if ch.get('title') == 'Длительность работы'),
                'Не указано'
            )
            description = project.get('descr', 'Описание отсутствует')

            formatted_projects.append(
                f"🔹 {title}\n"
                f"📌 Направление: {direction}\n"
                f"⏳ Длительность: {duration}\n"
                f"📝 {description}\n"
            )

        return formatted_projects if formatted_projects else ["Актуальные проекты не найдены"]

    except Exception as e:
        return [f"Error with projects: {str(e)}"]

# Отправление сообщение с клавиатуры.
def write_message(sender, message, keyboard=None):
    params = {
        'user_id': sender,
        'message': message,
        'random_id': get_random_id()
    }
    if keyboard:
        params['keyboard'] = keyboard

    authorize.method('messages.send', params)

# Здесь будут храниться вопросы и ответы на них.
faq_menu = []
faq_answers = {}

# Главное меню для начала взаимодействия с пользователем.
main_menu = [
    {'label': 'Частые вопросы', 'color': VkKeyboardColor.PRIMARY},
    {'label': 'Список курсов', 'color': VkKeyboardColor.POSITIVE},
    {'label': 'Про проекты', 'color': VkKeyboardColor.POSITIVE}
]

# Меню про проекты.
projects_menu = [
    {'label': 'Как выбрать проект?', 'color': VkKeyboardColor.PRIMARY},
    {'label': 'Что загружать в качестве проекта?', 'color': VkKeyboardColor.PRIMARY},
    {'label': 'Про сроки и формат проектов', 'color': VkKeyboardColor.PRIMARY},
    {'label': 'Примеры проектов', 'color': VkKeyboardColor.PRIMARY},
    {'label': 'Назад', 'color': VkKeyboardColor.NEGATIVE}
]


# Здесь хранятся вопросы и полученные с сайта ответы.
faq_menu, faq_answers = get_faq_data()

# Авторизация бота.
token = "here is your bot token"
authorize = vk_api.VkApi(token=token)
longpoll = VkLongPoll(authorize)

# Обработка сообщений.
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        sender = event.user_id
        received_message = event.text

        if received_message.lower() == "привет":
            write_message(sender,
                          "Добрый день! Выберите действие:",
                          create_keyboard(main_menu))

        elif received_message.lower() == "пока":
            write_message(sender, "До свидания!")

        elif received_message == "Список курсов":
            courses = get_vk_courses()
            response = "📚 Открытые курсы VK Education:\n" + "\n".join(courses)
            write_message(sender, response, create_keyboard(main_menu))

        elif received_message == "Частые вопросы":
            if not faq_menu:
                faq_menu, faq_answers = get_faq_data()

            if faq_menu:
                write_message(sender,
                              "Выберите интересующий вопрос:",
                              create_keyboard(faq_menu))
            else:
                write_message(sender,
                              "Не удалось загрузить вопросы.",
                              create_keyboard(main_menu))
        elif received_message == "Про проекты":
            write_message(sender,
                          "Выберите интересующий вопрос:",
                          create_keyboard(projects_menu))
        elif received_message == "Как выбрать проект?":
            write_message(sender,
                          "На выбор проекта могут влиять различные факторы: какое направление Вам нужно, какая область Вам интересна. " +
                          "Постарайтесь выделить для себя наиболее интересные работы и сделать выбор. Помните, что можно выполнять несколько проектов. " +
                          "Далее перейдите на страницу проекта и подайте заявку. (https://education.vk.company/education_projects)",
                          create_keyboard(projects_menu))
        elif received_message == "Что загружать в качестве проекта?":
            write_message(sender,
                          "Формат определяется отдельно в рамках каждого проекта.",
                          create_keyboard(projects_menu))
        elif received_message == "Про сроки и формат проектов":
            write_message(sender,
                          "Сроки определяются индивидуально в зависимости от задачи и Ваших целей.",
                          create_keyboard(projects_menu))
        elif received_message == "Примеры проектов":
            projects = get_projects()
            response = "📚 Открытые проекты VK Education:\n" + "\n".join(projects)
            write_message(sender, response, create_keyboard(projects_menu))
        elif received_message == "Назад":
            write_message(sender,
                          "Главное меню:",
                          create_keyboard(main_menu))

        elif received_message in faq_answers:
            answer = faq_answers[received_message]
            if len(answer) > 4096:
                answer = answer[:4000] + "...\n\n(сообщение сокращено)"
            write_message(sender, answer, create_keyboard(faq_menu))

        else:
            write_message(sender,
                          "Я не понимаю ваш запрос. Выберите действие из меню. Если вы не нашли ответа на свой вопрос" +
                          ", то свяжитесь с поддержкой на сайте VK Education: https://education.vk.company/contacts ",
                          create_keyboard(main_menu))