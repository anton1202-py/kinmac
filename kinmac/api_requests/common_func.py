import json
import time
import traceback

import telegram

from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, TELEGRAM_TOKEN

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def api_retry_decorator(func):
    def wrapper(*args, **kwargs):
        message = ''
        try:
            response = func(*args, **kwargs)
            for attempt in range(30):  # Попробуем выполнить запрос не более 30 раз
                response = func(*args, **kwargs)
                if response.status_code == 200:
                    if response.text:
                        json_response = json.loads(response.text)
                        return json_response
                    else:
                        return
                elif response.status_code == 204:
                    message = ''
                    return
                elif response.status_code == 403:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Доступ запрещен'
                elif response.status_code == 401:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Не авторизован'
                elif response.status_code == 404:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Страница не существует'
                elif response.status_code == 422:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Статус не изменился.'
                else:
                    time.sleep(10)  # Ждем 1 секунду перед повторным запросом
                if message:
                    bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID,
                                     text=message[:4000])
                    return

            message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}.'
            if message:
                bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID,
                                 text=message[:4000])
                return []
        except Exception as e:
            tb_str = traceback.format_exc()
            message_error = (f'Ошибка в функции: <b>{func.__name__}</b>\n'
                             f'<b>Функция выполняет</b>: {func.__doc__}\n'
                             f'<b>Ошибка</b>\n: {e}\n\n'
                             f'<b>Техническая информация</b>:\n {tb_str}')
            bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID,
                             text=message_error[:4000])
    return wrapper
