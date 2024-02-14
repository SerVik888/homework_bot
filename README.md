# Проект homework_bot(python_telegram_bot)

### Описание проекта:
API сервиса Практикум.Домашка позволяет отслеживать изменение статуса домашней работы на ревью.\
Доступ к API возможен только по токену, который можно получить по адресу https://oauth.yandex.ru/authorize.\
Ревьюер присваивает работе один из статусов: работа принята на проверку, работа возвращена для исправления ошибок, работа принята.\
С помощью API можно получить список домашних работ с актуальными статусами за период от from_date до настоящего момента.\
Для успешного запроса нужно передать токен авторизации и метку времени в формате Unix time в заголовке запроса и GET-параметре соответственно.\
API возвращает ответы в формате JSON, где ключом homeworks является список домашних работ, а ключом current_date - время отправки ответа.\
Статусы домашней работы могут быть трех типов: reviewing, approved, rejected.

### Как запустить проект:

`git clone git@github.com:SerVik888/homework_bot.git` -> клонировать репозиторий

`cd homework_bot` -> перейти в папку

* Если у вас Linux/macOS\
    `python3 -m venv env` -> создать виртуальное окружение\
    `source env/bin/activate` -> активировать виртуальное окружение\
    `python3 -m pip install --upgrade pip` -> обновить установщик\
    `pip install -r requirements.txt` -> установить зависимости из файла requirements.txt\
    `python3 homework.py` -> запуск бота\

* Если у вас windows\
    `python -m venv env` -> создать виртуальное окружение\
    `source venv/Scripts/activate` -> активировать виртуальное окружение\
    `python -m pip install --upgrade pip` -> обновить установщик\
    `pip install -r requirements.txt` -> установить зависимости из файла requirements.txt\
    `python homework.py` -> запуск бота\

### Как тестировать проект
`source venv/Scripts/activate` -> активировать виртуальное окружение\
`pytest` -> Выполнить команду из корня проекта

### Cписок используемых технологий
- pytest
- python-dotenv
- python-telegram-bot

### Как заполнить файл .env:
В проекте есть файл .env.example заполните свой по аналогии.

`PRACTICUM_TOKEN` - токен для доступа к эндпоинту https://practicum.yandex.ru/api/user_api/homework_statuses/(API Практикум.Домашка)\
`TELEGRAM_TOKEN` - токен для работы с Bot API\
`TELEGRAM_CHAT_ID` - это ID того чата, в который бот должен отправить сообщение\

Автор: Сафонов Сергей\
Почта: [sergey_safonov86@inbox.ru](mailto:sergey_safonov86@inbox.ru)