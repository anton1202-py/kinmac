import json
import os
import traceback
from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
import psycopg2
import requests
import telegram
#from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def test_foo():

        while True:
            api_url = "https://api-seller.ozon.ru/v2/product/list
            headers = {
                'Client-Id': OZON_ID,
                'Api-Key': TOKEN_OZON
            }

            payload = json.dumps({
              "filter": {
                "offer_id": [],
                "product_id": [],
                "visibility": "ALL"
              },
              "last_id": "",
              "limit": 5
            })
            response = requests.post(api_url, headers=headers, data=payload)
            if response.status_code == 200:
                print('response.status_code', response.status_code)
                data = response.json()
                products = data.get("result", {}).get("items", [])
                if not products:
                    break  # Выход из цикла, если продукты закончились

                products_ids = [product["product_id"] for product in products]
                print(len(products_ids))
                for product_id in products_ids:
                    response_info = requests.post("https://api-seller.ozon.ru/v2/product/info/list",
                                                  json={"product_id": [product_id]}, headers=headers)
                    print('product_id', product_id)
                    # print('response_info.json().get("result", {}).get("items", [])', response_info.json().get("result", {}).get("items", []))
                    print('response_info.status_code', response_info.status_code)
                    if response_info.status_code != 200:

                        print(f"Ошибка при получении данных по продукту: {product_id}")
                        continue  # Пропускаем продукт с ошибкой

                    response_info = response_info.json().get("result", {}).get("items", [])
                    
test_foo()