import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

from exception import BadRequest, MissingKeyInResponse, RequestError

PATH_FOR_LOGS = os.path.dirname(os.path.abspath(__file__)) + '/logs.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(PATH_FOR_LOGS, mode='a', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s '
    '%(filename)s/%(funcName)s/%(lineno)d '
    '[%(levelname)s] '
    '%(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logger.critical(
            'Бот не может отправить сообщение т.к. нет переменной'
            ' окружения. Программа принудительно остановлена!'
        )
        sys.exit('Отсутствует переменная окружения!!!')


def send_message(bot, message):
    """Отправляем сообщение в Telegram чат.
    Определяемый переменной окружения TELEGRAM_CHAT_ID.
    """
    logger.debug('Начало отправки сообщения в Telegram.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logger.error(f'Cбой при отправке сообщения в Telegram. {error}')
    else:
        logger.debug('Удачная отправка сообщения в Telegram.')


def get_api_answer(timestamp):
    """Делаем запрос к  API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    request_data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    logger.debug(
        'Начало отправки запроса к {url}, '
        'c параметрами: {params}'
        .format(**request_data)
    )
    try:
        response = requests.get(**request_data)
    except RequestException:
        raise RequestError(
            'Ошибка при запросе к {url}, '
            'c параметрами: {params}'.format(**request_data)
        )

    if response.status_code != HTTPStatus.OK:
        logger.error(
            f'Код ответа {response.status_code}, ожидалось {HTTPStatus.OK}.'
        )
        raise BadRequest(
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен.'
            f' Код ответа API: {response.status_code}'
        )
    return response.json()


def check_response(response):
    """Проверяем ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError(
            f'Тип данных в ответе {type(response)}'
            ' не соответствует ожидаемому типу dict'
        )
    if 'homeworks' not in response:
        raise MissingKeyInResponse(
            'Отсутствует ключ homeworks в ответе API.'
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            'Тип данных в ответе не соответствует ожидаемому типу list'
        )
    if 'current_date' not in response:
        raise MissingKeyInResponse(
            'Отсутствует ключ current_date в ответе API.'
        )
    return homeworks


def parse_status(homework):
    """Извлекаем информацию о конкретной домашней работе.
    В случае успеха, возвращаем подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS.
    """
    if 'status' not in homework:
        raise KeyError(
            'Не найден ключ homework_name.'
        )
    if 'homework_name' not in homework:
        raise KeyError(
            'Не найден ключ homework_name.'
        )
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError(
            'Статус не найден.'
        )
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    old_status = ''
    new_status = ''

    while True:

        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date', timestamp)
            homeworks = check_response(response)
            if homeworks:
                new_status = parse_status(homeworks[0])
            else:
                new_status = ('Статус работые не изменился')

            if old_status != new_status:
                send_message(bot, new_status)
                old_status = new_status
            else:
                logger.debug('Нет новых статусов')

        except MissingKeyInResponse as error:
            logger.error(error)

        except Exception as error:
            new_status = f'Сбой в работе программы: {error}'
            if old_status != new_status:
                logger.error(new_status)
                send_message(bot, new_status)
                old_status = new_status

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
