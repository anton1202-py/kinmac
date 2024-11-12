import os

import telegram
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'kinmac', '.env')
load_dotenv(dotenv_path)

STATISTIC_WB_TOKEN = os.getenv('STATISTIC_WB_TOKEN')
WB_COMMON_KEY = os.getenv('WB_COMMON_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WB_COOKIE = os.getenv('WB_COOKIE')

TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID')

wb_headers = {
    'Content-Type': 'application/json',
    'Authorization': WB_COMMON_KEY
}

wb_header_with_lk_cookie = {
    'authorizev3': '',
    'baggage': '',
    'cookie': WB_COOKIE,
    'sentry-trace': '',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 YaBrowser/24.10.0.0 Safari/537.36',
    'Content-Type': 'application/json'
}

BRAND_LIST = ['KINMAC', 'Allonsy']
bot = telegram.Bot(token=TELEGRAM_TOKEN)

actions_info_users_list = []
