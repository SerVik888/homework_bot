# from datetime import time
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import os
# from time import sleep, time
import time

import requests
from requests import HTTPError, RequestException
from dotenv import load_dotenv
from telegram.error import TelegramError
import telegram
from telegram.ext import CommandHandler, Updater

from exception import EnvironmentVariableError, InvalidResponse, StatusError, UnknownError

# ??? Как переместить новые исключения в except ???
# ??? Переделать все исключения ???
# ??? Незабыть поменять время отправки на константу???
# Добавить timestamp
# Удалить файлы логов
# Нарисать логирование везде где выбрасываю исключения

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(
)
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
    """Функция check_tokens() проверяет доступность переменных окружения, 
    которые необходимы для работы программы. 
    Если отсутствует хотя бы одна переменная окружения — продолжать работу бота нет смысла."""
    try:
        if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            raise EnvironmentVariableError(
                'Бот не может отправить сообщение т.к.'
                ' нет переменной окружения. Программа принудительно остановлена!'
            )
    except EnvironmentVariableError as error:
        logger.critical(error)
        exit()


def send_message(bot, message):
    """Функция send_message() отправляет сообщение в Telegram чат, 
       определяемый переменной окружения TELEGRAM_CHAT_ID.
      Принимает на вход два параметра: экземпляр класса Bot и строку с текстом сообщения."""

    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Удачная отправка сообщения в Telegram.')
    except TelegramError as error:
        logger.ERROR(error)
        raise TelegramError(error)
    except RequestException:
        logging.error('Cбой при отправке сообщения в Telegram.')
    # if message not in HOMEWORK_VERDICTS.values():
    #     raise RequestException('Статус не найден.')
    # return message


def get_api_answer(timestamp):
    """Функция get_api_answer() делает запрос к единственному эндпоинту API-сервиса.
      В качестве параметра в функцию передается временная метка. 
      В случае успешного запроса должна вернуть ответ API, 
    приведя его из формата JSON к типам данных Python."""
    # TODO Я так и не понял как работает эта конструкция, я думал все иксключения
    # TODO будут попадать в RequestException,
    # TODO а туту мы почему то можем делать проверку уже после отлова исключений
    # response = requests.get(
    #     ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
    # )
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
    except TelegramError as error:
        logging.error(error)
    except RequestException as error:
        logger.error(error)

    if response.status_code != 200:
        logger.error('Ошибка')
        raise HTTPError(
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. Код ответа API: {response.status_code}'
        )
    return response.json()


def check_response(response):
    """Функция check_response() проверяет ответ API на соответствие документации 
    из урока API сервиса Практикум.Домашка. В качестве параметра функция получает ответ API, 
    приведенный к типам данных Python."""
    # typesde = type(response)

    if type(response) is not dict:
        logger.error('Ошибка')
        raise TypeError(
            f'Тип данных в ответе {type(response)} не соответствует ожидаемому типу dict'
        )
    elif 'homeworks' not in response:
        logger.error('Ошибка')
        raise KeyError('Отсутствует ключ homeworks в ответе API.')
    elif type(response['homeworks']) is not list:
        logger.error('Ошибка')
        raise TypeError(
            f'Тип данных в ответе не соответствует ожидаемому типу list'
        )
    elif 'current_date' not in response:
        logger.error('Ошибка')
        raise KeyError('Отсутствует ключ current_date в ответе API.')


def parse_status(homework):
    """Функция parse_status() извлекает из информации о конкретной домашней работе 
    статус этой работы. В качестве параметра функция 
    получает только один элемент из списка домашних работ. 
    В случае успеха, функция возвращает подготовленную для отправки в Telegram строку, 
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS."""
    # prev_status = ''
    if homework['status'] not in HOMEWORK_VERDICTS:
        logger.error('Ошибка')
        raise RequestException('Статус не найден.')
    elif 'homework_name' not in homework:
        logger.error('Ошибка')
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
    response = get_api_answer(1686182400)
    check_response(response)

    while True:
        # time.sleep(5)
        time.sleep(RETRY_PERIOD)

        try:

            homework = response['homeworks'][LAST_HOMEWORK]
            message = parse_status(homework)
            for value in HOMEWORK_VERDICTS.values():
                if value in message and homework['status'] != old_status:
                    logger.warn('Статус работы изменился.')
                    send_message(bot, message)
                    old_status = homework['status']
            if homework['status'] == old_status:
                logger.warn('Статус работы изменился.')
        # except TelegramError as error:
        #     logger.error(f'Cбой при отправке сообщения в Telegram. {error}')
        # except KeyError as error:
        #     logger.error(f'Cбой при отправке сообщения в Telegram. {error}')
        # except TypeError as error:
        #     logger.error(f'Cбой при отправке сообщения в Telegram. {error}')
        except RequestException as error:

            message = f'Сбой в работе программы: {error}'
            if message == old_message:
                logger.error(message)
            # send_message(bot, message)
            else:
                logger.error(message)
                send_message(bot, message)
                old_message = message
        # ...


if __name__ == '__main__':
    main()
