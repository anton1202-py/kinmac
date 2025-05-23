import json
import time
import requests
from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, bot


class OzonTemplatesRequest:

    def _post_template_req(self, url: str, header: dict, payload: str) -> dict:
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)
        elif response.status_code == 403:
            message = (
                "Статус код 403 при запросе кз фронт "
                "у загрузки стоимости хранения"
            )
            bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message)

    def _get_template_req(self, url: str, header: dict) -> dict | str:
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            return json.loads(response.text)
        else:

            message: str = (
                f"Статус код: {response.status_code} "
                f"на запрос {url}. Ошибка: {response.text}"
            )
            bot.send_message(
                chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000]
            )
            return message

    def _post_recursion_template_last_id_req(
        self, url: str, header: dict, limit=1000, last_id="", data_list=None
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {
                "filter": {
                    "offer_id": [],
                    "product_id": [],
                    "visibility": "ALL",
                },
                "last_id": last_id,
                "limit": limit,
            }
        )
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["result"]["items"]
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                last_id = main_data["result"]["last_id"]
                return self._post_recursion_template_last_id_req(
                    url, header, limit, last_id, data_list
                )
            else:
                return data_list


class ArticleDataRequest:

    def __init__(self):
        self.MAIN_URL = "https://api-seller.ozon.ru/"

    def _post_template_req(self, url: str, header: dict, payload: str) -> dict:
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)

    def _post_recursion_template_req(
        self, url: str, header: dict, limit=1000, last_id="", data_list=None
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {
                "filter": {
                    "offer_id": [],
                    "product_id": [],
                    "visibility": "ALL",
                },
                "last_id": last_id,
                "limit": limit,
            }
        )
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["result"]["items"]
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                last_id = main_data["result"]["last_id"]
                return self._post_recursion_template_req(
                    url, header, limit, last_id, data_list
                )
            else:
                return data_list

    def _post_recursion_attribute_template_req(
        self, url: str, header: dict, limit=1000, last_id="", data_list=None
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {
                "filter": {
                    "offer_id": [],
                    "product_id": [],
                    "sku": [],
                    "visibility": "ALL",
                },
                "last_id": last_id,
                "limit": limit,
            }
        )
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["result"]
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                last_id = main_data["last_id"]
                return self._post_recursion_template_req(
                    url, header, limit, last_id, data_list
                )
            else:
                return data_list

    def ozon_products_list(self, header: dict) -> list:
        url = f"{self.MAIN_URL}v3/product/list"
        return self._post_recursion_template_req(url, header)

    def ozon_product_info(
        self, header: dict, products: list = None, sku: list = None
    ) -> dict:
        url = f"{self.MAIN_URL}v3/product/info/list"
        if products is None:
            products = []
        if sku is None:
            sku = []
        payload = json.dumps(
            {"offer_id": [], "product_id": products, "sku": sku}
        )
        return self._post_template_req(url, header, payload)

    def ozon_product_attributes(self, header: dict) -> list:
        url = f"{self.MAIN_URL}v4/product/info/attributes"
        return self._post_recursion_attribute_template_req(url, header)


class ActionRequest(OzonTemplatesRequest):

    def __init__(self):
        self.MAIN_URL = "https://api-seller.ozon.ru/"

    def _post_recursion_template_req_action(
        self,
        url: str,
        header: dict,
        action_id: int,
        limit=1000,
        offset=0,
        attempt=1,
        data_list=None,
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {"limit": limit, "offset": offset, "action_id": action_id}
        )
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["result"]["products"]
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                offset = limit * attempt
                attempt += 1
                return self._post_recursion_template_req_action(
                    url, header, limit, offset, attempt, data_list
                )
            else:
                return data_list

    def actions_list(self, header: dict) -> dict:
        url = f"{self.MAIN_URL}v1/actions"
        return self._get_template_req(url, header)

    def access_products_for_action(self, header: dict, action_id: int) -> list:
        url = f"{self.MAIN_URL}v1/actions/candidates"
        return self._post_recursion_template_req_action(url, header, action_id)

    def hotsale_actions_list(self, header: dict) -> dict:
        url = f"{self.MAIN_URL}v1/actions/hotsales/list"
        payload = json.dumps({})
        return self._post_template_req(url, header, payload)

    def products_in_hotsale(self, header: dict, action_id: int) -> list:
        url = f"{self.MAIN_URL}v1/actions/hotsales/products"
        return self._post_recursion_template_req_action(url, header, action_id)


class OzonSalesRequest(OzonTemplatesRequest):

    def __init__(self):
        self.main_url = "https://api-seller.ozon.ru/"

    def _post_recursion_template_req(
        self,
        url: str,
        header: dict,
        date_from: str,
        date_to: str,
        limit=1000,
        offset=0,
        attempt=1,
        data_list=None,
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {
                "dir": "ASC",
                "filter": {
                    "since": f"{date_from}T00:00:00.878Z",
                    "to": f"{date_to}T23:59:59.878Z",
                    "status": "delivered",
                },
                "limit": limit,
                "offset": offset,
                "with": {"financial_data": True},
            }
        )
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["result"]
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                offset = limit * attempt
                attempt += 1
                return self._post_recursion_template_req(
                    url=url,
                    header=header,
                    date_from=date_from,
                    date_to=date_to,
                    limit=limit,
                    offset=offset,
                    attempt=attempt,
                    data_list=data_list,
                )
            else:
                return data_list

    def realization_report(self, header: dict, month: int, year: int) -> dict:
        url = f"{self.main_url}v2/finance/realization"
        payload = json.dumps({"month": month, "year": year})
        return self._post_template_req(url, header, payload)

    def daily_orders_req(self, header: dict, check_date: str) -> dict:
        url = f"{self.main_url}v1/analytics/data"
        payload = json.dumps(
            {
                "date_from": check_date,
                "date_to": check_date,
                "metrics": ["revenue", "ordered_units"],
                "dimension": ["sku"],
                "limit": 1000,
                "offset": 0,
            }
        )
        return self._post_template_req(url, header, payload)

    def fbs_orders_req(self, header: dict, date_from: str, date_to: str):
        """Заказы FBS"""
        url = f"{self.main_url}v3/posting/fbs/list"
        payload = json.dumps(
            {
                "dir": "ASC",
                "filter": {
                    "since": f"{date_from}T00:00:00.878Z",
                    "to": f"{date_to}T23:59:59.878Z",
                    "status": "delivered",
                },
                "limit": 1000,
                "offset": 0,
                "with": {"financial_data": True},
            }
        )
        return self._post_template_req(url, header, payload)

    def fbo_orders_req(
        self, header: dict, date_from: str, date_to: str
    ) -> list:
        """Заказы FBO"""
        url = f"{self.main_url}v2/posting/fbo/list"
        return self._post_recursion_template_req(
            url=url, header=header, date_from=date_from, date_to=date_to
        )


class OzonWarehouseApiRequest:
    def __init__(self):
        self.main_url = "https://api-seller.ozon.ru/"

    def _post_template_req(self, url: str, header: dict, payload: str) -> dict:
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)

    def _post_recursion_template_req(
        self,
        url: str,
        header: dict,
        limit=1000,
        offset=0,
        attempt=1,
        data_list=None,
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {"limit": limit, "offset": offset, "warehouse_type": "ALL"}
        )
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["result"]["rows"]
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                offset = limit * attempt
                attempt += 1
                return self._post_recursion_template_req(
                    url, header, limit, offset, attempt, data_list
                )
            else:
                return data_list

    def cluster_warehouse_req(self, header: dict):
        url = f"{self.main_url}v1/cluster/list"
        payload = json.dumps({"cluster_type": "CLUSTER_TYPE_OZON"})
        return self._post_template_req(url, header, payload)

    def warehouse_stock_req(self, header: dict):
        url = f"{self.main_url}v2/analytics/stock_on_warehouses"
        return self._post_recursion_template_req(url, header)


class OzonAdvertismentApiRequest:
    def __init__(self):
        self.main_url = "https://api-performance.ozon.ru:443/"

    def _post_template_req(
        self, url: str, header: dict, payload: str
    ) -> dict | str:
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)
        elif response.status_code == 429:
            time.sleep(65)
            return self._post_template_req(
                url=url, header=header, payload=payload
            )
        else:
            message = (
                f"Статус код: {response.status_code} "
                f"на запрос {url}. Ошибка: {response.text}"
            )
            bot.send_message(
                chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000]
            )
            return message

    def _get_template_req(self, url: str, header: dict) -> dict | str:
        response = requests.request("GET", url, headers=header)
        if response.status_code == 200:
            return json.loads(response.text)
        else:

            message = (
                f"Статус код: {response.status_code} "
                f"на запрос {url}. Ошибка: {response.text}"
            )
            bot.send_message(
                chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000]
            )
            return message

    def _post_recursion_template_req(
        self,
        url: str,
        header: dict,
        limit=1000,
        offset=0,
        attempt=1,
        data_list=None,
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {"limit": limit, "offset": offset, "warehouse_type": "ALL"}
        )
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["result"]["rows"]
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                offset = limit * attempt
                attempt += 1
                return self._post_recursion_template_req(
                    url, header, limit, offset, attempt, data_list
                )
            else:
                return data_list

    def get_auth_header(
        self, header: dict, perfomance_header: dict
    ) -> dict | str:
        url = f"{self.main_url}/api/client/token"
        payload = json.dumps(perfomance_header)
        data = self._post_template_req(url, header, payload)
        if isinstance(data, dict):
            token = f"Bearer {data['access_token']}"
            header = {
                "Content-Type": "application/json",
                "Authorization": token,
            }
            return header
        else:
            message = (
                f"Ошибка при получении токена авторизации "
                f"к рекламному кабинету. Текст: {data}"
            )
            bot.send_message(
                chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000]
            )
            return message

    def get_proxy_auth_post_request(
        self, header: dict, perfomance_header: dict, url: str, payload: dict
    ) -> dict:
        auth_header = self.get_auth_header(header, perfomance_header)
        data = self._post_template_req(url, auth_header, payload)
        return data

    def get_proxy_auth_get_request(
        self, header: dict, perfomance_header: dict, url: str
    ) -> dict:
        auth_header = self.get_auth_header(header, perfomance_header)
        data = self._get_template_req(url, auth_header)
        return data

    def create_trafarets_top_campaign_req(
        self,
        header: dict,
        perfomance_header: dict,
        title: str,
        placement: str,
        product_auto_strategy: str,
    ) -> dict:
        """
        Создание кампаний ТРАФАРЕТ или ВЫВОД В ТОП
        Default: "PLACEMENT_INVALID"
        Место размещения продвигаемых товаров:

        PLACEMENT_TOP_PROMOTION — вывод в топ.
        PLACEMENT_INVALID — не определено.
        PLACEMENT_SEARCH_AND_CATEGORY — поиск и категории (Трафареты).
        """
        url = f"{self.main_url}api/client/campaign/cpc/v2/product"
        payload = json.dumps(
            {
                "title": title,
                "weeklyBudget": 7_000_000_000,
                "placement": placement,
                "productAutopilotStrategy": product_auto_strategy,
            }
        )
        return self.get_proxy_auth_post_request(
            header, perfomance_header, url, payload
        )

    def activate_trafarets_top_campaign_req(
        self, header: dict, perfomance_header: dict, campaign_id: str
    ) -> dict:
        """
        Активация кампании
        """
        url = f"{self.main_url}api/client/campaign/{campaign_id}/activate"
        payload = json.dumps({})
        return self.get_proxy_auth_post_request(
            header, perfomance_header, url, payload
        )

    def stop_trafarets_top_campaign_req(
        self, header: dict, perfomance_header: dict, campaign_id: str
    ) -> dict:
        """
        Выключить кампанию
        """
        url = f"{self.main_url}api/client/campaign/{campaign_id}/deactivate"
        payload = json.dumps({})
        return self.get_proxy_auth_post_request(
            header, perfomance_header, url, payload
        )

    def add_products_to_trafarets_top_campaign_req(
        self,
        header: dict,
        perfomance_header: dict,
        campaign_id: str,
        sku_bid_info: dict,
    ) -> None:
        """
        Добавить товары в кампанию
        """
        url = f"{self.main_url}api/client/campaign/{campaign_id}/products"
        payload = json.dumps({"bids": [sku_bid_info]})
        return self.get_proxy_auth_post_request(
            header, perfomance_header, url, payload
        )

    def add_products_to_search_promo_req(
        self, header: dict, perfomance_header: dict, ozon_sku: str
    ) -> dict:
        """
        Включить продвижение товара в поиске
        """
        url = f"{self.main_url}api/client/search_promo/product/enable"
        payload = json.dumps({"skus": [ozon_sku]})
        return self.get_proxy_auth_post_request(
            header, perfomance_header, url, payload
        )

    def campaigns_list_req(
        self, header: dict, perfomance_header: dict
    ) -> dict:
        """
        Список кампаний
        """
        url = f"{self.main_url}api/client/campaign"
        return self.get_proxy_auth_get_request(header, perfomance_header, url)

    def products_in_campaign_req(
        self, header: dict, perfomance_header: dict, campaign_id: str
    ) -> dict:
        """
        Список артикулов в кампании
        """
        url = f"{self.main_url}api/client/campaign/{campaign_id}/objects"
        return self.get_proxy_auth_get_request(header, perfomance_header, url)

    def products_in_trafaret_top_campaign_req(
        self, header: dict, perfomance_header: dict, campaign_id: str
    ) -> dict:
        """
        Список артикулов в кампании
        """
        url = f"{self.main_url}api/client/campaign/{campaign_id}/v2/products"
        return self.get_proxy_auth_get_request(header, perfomance_header, url)

    def products_in_search_promo_campaign_req(
        self, header: dict, perfomance_header: dict
    ) -> dict:
        """
        Список артикулов в кампании
        """
        url = f"{self.main_url}api/client/campaign/search_promo/v2/products"
        payload = json.dumps({"page": 0, "pageSize": 1000})
        return self.get_proxy_auth_post_request(
            header, perfomance_header, url, payload
        )

    def add_product_to_search_promo_campaign_req(
        self, header: dict, perfomance_header: dict, sku: str
    ) -> dict:
        """
        Добавить артикул в продвижение в поиске
        """
        url = f"{self.main_url}api/client/search_promo/product/enable"
        payload = json.dumps({"skus": [sku]})
        return self.get_proxy_auth_post_request(
            header, perfomance_header, url, payload
        )

    def cost_statistic(
        self,
        header: dict,
        perfomance_header: dict,
        date_from: str,
        date_to: str,
    ):
        """
        Статистика расходов рекламных кампаний
        """
        url = (
            f"{self.main_url}api/client/statistics/expense/"
            f"json?dateFrom={date_from}&dateTo={date_to}"
        )
        return self.get_proxy_auth_get_request(header, perfomance_header, url)

    def search_promo_report(
        self,
        header: dict,
        perfomance_header: dict,
        date_from: str,
        date_to: str,
    ) -> dict:
        """
        Отчёт по заказам в продвижении в поиске
        """
        method = "/api/client/statistic/orders/generate/json"
        payload = json.dumps(
            {"from": f"{date_from}T00:00:00Z", "to": f"{date_to}T00:00:00Z"}
        )
        return self.get_proxy_auth_post_request(
            header, perfomance_header, self.main_url + method, payload
        )

    def check_report_status(
        self,
        header: dict,
        perfomance_header: dict,
        report_uuid: str,
    ) -> dict:
        """
        Проверить статус формирования отчета
        """
        method = f"/api/client/statistics/{report_uuid}"

        return self.get_proxy_auth_get_request(
            header, perfomance_header, self.main_url + method
        )

    def get_report(
        self,
        header: dict,
        perfomance_header: dict,
        report_uuid: str,
    ) -> dict:
        """
        Получить отчёты
        """
        method = f"/api/client/statistics/report?UUID={report_uuid}"

        return self.get_proxy_auth_get_request(
            header, perfomance_header, self.main_url + method
        )


class OzonPriceComissionApiRequest(OzonTemplatesRequest):

    def __init__(self):
        self.main_url = "https://api-seller.ozon.ru/"

    def _post_recursion_template_req_action(
        self,
        url: str,
        header: dict,
        data_list: list = None,
        limit: int = 1000,
        cursor: str = "",
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {
                "cursor": cursor,
                "filter": {
                    "offer_id": [],
                    "product_id": [],
                    "visibility": "ALL",
                },
                "limit": limit,
            }
        )
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            main_data = json.loads(response.text)
            response_data = main_data["items"]
            for data in response_data:
                data_list.append(data)
            if main_data["total"] == limit:
                cursor = main_data["cursor"]
                return self._post_recursion_template_req_action(
                    url=url,
                    header=header,
                    limit=limit,
                    data_list=data_list,
                    cursor=cursor,
                )
            else:
                return data_list

    def comission_price_req(self, header: dict) -> list:
        """Запрос по комиссиям и актуальной цене"""
        url = f"{self.main_url}v5/product/info/prices"
        return self._post_recursion_template_req_action(url, header)


class OzonReportsApiRequest(OzonTemplatesRequest):

    def __init__(self):
        self.url = "https://api-seller.ozon.ru"

    def _post_recursion_template_req_transaction(
        self,
        url: str,
        header: dict,
        date_from: str,
        date_to: str,
        data_list: list = None,
        posting_number: str = "",
        limit: int = 1000,
        page: int = 1,
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {
                "filter": {
                    "date": {
                        "from": f"{date_from}T00:00:00.000Z",
                        "to": f"{date_to}T00:00:00.000Z",
                    },
                    "posting_number": posting_number,
                    "transaction_type": "all",
                },
                "page": page,
                "page_size": limit,
            }
        )
        response = requests.post(url, headers=header, data=payload)
        if response.status_code == 200:
            main_data: dict = json.loads(response.text).get("result")
            response_data: list = main_data.get("operations")
            for data in response_data:
                data_list.append(data)
            if len(response_data) == limit:
                page += 1
                return self._post_recursion_template_req_transaction(
                    url=url,
                    header=header,
                    date_from=date_from,
                    date_to=date_to,
                    data_list=data_list,
                    limit=limit,
                    page=page,
                )
            else:
                return data_list

    def finance_transaction_list(
        self,
        header: dict,
        date_from: str,
        date_to: str,
        posting_number: str = "",
    ) -> list[dict]:
        """
        Возвращает подробную информацию по всем начислениям.
        Максимальный период, за который можно получить информацию
        в одном запросе — 1 месяц.
        """
        method = "/v3/finance/transaction/list"
        return self._post_recursion_template_req_transaction(
            url=self.url + method,
            header=header,
            date_from=date_from,
            date_to=date_to,
            posting_number=posting_number,
        )


class OzonFrontApiRequests(OzonTemplatesRequest):

    def __init__(self):
        self.url: str = "https://seller.ozon.ru"

    def daily_storage_cost(self, front_header: dict, check_date: str) -> dict:
        """."""
        time.sleep(15)
        method = (
            "/api/site/self-placement-gateway/placement/periods/date/items"
        )
        payload = json.dumps(
            {
                "pagination": {"page": 1, "page_size": 1000},
                "sorting": {
                    "sort_by": "ByAccountingPlacement",
                    "sort_direction": "Desc",
                },
                "billed_type": "Paid",
                "date": check_date,
            }
        )
        return self._post_template_req(
            url=self.url + method, header=front_header, payload=payload
        )

    def page_prices_info(
        self, front_header: dict, front_company_id: str, prodict_ids: list[str]
    ) -> dict:
        """
        Получает инфо со страницы с ценами товара.
        Цена продавца, цена для покупателя, цена с картой Озон.
        """
        time.sleep(15)
        method = "/api/pricing-bff-service/v3/get-common-prices"
        payload = json.dumps(
            {"company_id": front_company_id, "item_ids": prodict_ids}
        )
        return self._post_template_req(
            url=self.url + method, header=front_header, payload=payload
        )


"""Загружать /v1/finance/cash-flow-statement/list"""
