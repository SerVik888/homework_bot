import logging
import os
import time

import requests
from requests import HTTPError, RequestException
from dotenv import load_dotenv
import telegram

from exception import EnvironmentVariableError


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

LAST_HOMEWORK = -1
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяем доступность переменных окружения.
    Которые необходимы для работы программы.
    """
    try:
        if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            raise EnvironmentVariableError(
                'Бот не может отправить сообщение т.к. нет переменной'
                ' окружения. Программа принудительно остановлена!'
            )
    except EnvironmentVariableError as error:
        logger.critical(error)
        exit()


def send_message(bot, message):
    """Отправляем сообщение в Telegram чат.
    Определяемый переменной окружения TELEGRAM_CHAT_ID.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Удачная отправка сообщения в Telegram.')
    except telegram.TelegramError as error:
        logger.error(f'Cбой при отправке сообщения в Telegram. {error}')


def get_api_answer(timestamp):
    """Делаем запрос к  API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    # TODO Я так и не понял как работает эта конструкция,
    # я думал все иксключения будут попадать в RequestException,
    # а туту мы почему то можем делать проверку уже после отлова
    # исключений

    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
    except RequestException as error:
        logger.error(error)

    if response.status_code != 200:
        logger.error('Ошибка')
        raise HTTPError(
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен.'
            f' Код ответа API: {response.status_code}'
        )
    return response.json()


def check_response(response):
    """Проверяем ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    if type(response) is not dict:
        raise TypeError(
            f'Тип данных в ответе {type(response)}'
            f' не соответствует ожидаемому типу dict'
        )
    elif 'homeworks' not in response:
        raise KeyError('Отсутствует ключ homeworks в ответе API.')
    elif type(response['homeworks']) is not list:
        raise TypeError(
            'Тип данных в ответе не соответствует ожидаемому типу list'
        )
    elif 'current_date' not in response:
        raise KeyError('Отсутствует ключ current_date в ответе API.')


def parse_status(homework):
    """Извлекаем информацию о конкретной домашней работе.
    В случае успеха, возвращаем подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS.
    """
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise RequestException('Статус не найден.')
    elif 'homework_name' not in homework:
        raise RequestException('Не найден ключ homework_name.')

    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    old_message = ''
    old_status = ''
    response = get_api_answer(timestamp)
    check_response(response)

    while True:

        try:
            homework = response['homeworks'][LAST_HOMEWORK]
            message = parse_status(homework)
            for value in HOMEWORK_VERDICTS.values():
                if value in message and homework['status'] != old_status:
                    logger.debug('Статус работы изменился.')
                    send_message(bot, message)
                    old_status = homework['status']
            if homework['status'] == old_status:
                logger.debug('Статус работы не изменился.')
        except IndexError:
            logger.debug('Работа не принята на проверку')
        except RequestException as error:
            message = f'Сбой в работе программы: {error}'
            if message == old_message:
                logger.error(message)
            else:
                logger.error(message)
                send_message(bot, message)
                old_message = message

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
