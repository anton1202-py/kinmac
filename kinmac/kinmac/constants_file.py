import os

import telegram
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'kinmac', '.env')
load_dotenv(dotenv_path)

STATISTIC_WB_TOKEN = os.getenv('STATISTIC_WB_TOKEN')
WB_COMMON_KEY = os.getenv('WB_COMMON_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

wb_headers = {
    'Content-Type': 'application/json',
    'Authorization': WB_COMMON_KEY
}

BRAND_LIST = ['KINMAC', 'Allonsy']
bot = telegram.Bot(token=TELEGRAM_TOKEN)