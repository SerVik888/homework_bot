
class EnvironmentVariableError(Exception):
    """Исключение при отсутствии одной из переменных окружения."""

    pass


class RequestError(Exception):
    """Исключение при получении данных из эндпоинта."""

    pass


class BadRequest(Exception):
    """Исключение при получении кода статуса отличного от 200."""

    pass


class MissingKeyInResponse(Exception):
    """Исключение при отсутствии какого-либо ключа в ответе."""

    pass
