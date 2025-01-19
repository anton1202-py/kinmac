import json
import requests
from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, bot


class OzonTemplatesRequest:

    def _post_template_req(self, url: str, header: dict, payload: str) -> dict:
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)


class ArticleDataRequest:

    def __init__(self):
        self.MAIN_URL = "https://api-seller.ozon.ru/"

    def _post_template_req(self, url: str, header: dict, payload: str) -> dict:
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)

    def _post_recursion_template_req(
        self, url: str, header: dict, limit=1000, last_id="", data_list=None
    ) -> list:
        if not data_list:
            data_list = []
        payload = json.dumps(
            {
                "filter": {"offer_id": [], "product_id": [], "visibility": "ALL"},
                "last_id": last_id,
                "limit": limit,
            }
        )
        response = requests.request("POST", url, headers=header, data=payload)
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

    def ozon_products_list(self, header: dict) -> list:
        url = f"{self.MAIN_URL}v2/product/list"
        return self._post_recursion_template_req(url, header)

    def ozon_product_info(
        self, header: dict, products: list = None, sku: list = None
    ) -> dict:
        url = f"{self.MAIN_URL}v3/product/info/list"
        if products is None:
            products = []
        if sku is None:
            sku = []
        payload = json.dumps({"offer_id": [], "product_id": products, "sku": sku})
        return self._post_template_req(url, header, payload)


class OzonSalesRequest(OzonTemplatesRequest):

    def __init__(self):
        self.MAIN_URL = "https://api-seller.ozon.ru/"

    def realization_report(self, header: dict, month: int, year: int) -> dict:
        url = f"{self.MAIN_URL}v2/finance/realization"
        payload = json.dumps({"month": month, "year": year})
        return self._post_template_req(url, header, payload)


class OzonWarehouseApiRequest:
    def __init__(self):
        self.main_url = "https://api-seller.ozon.ru/"

    def _post_template_req(self, url: str, header: dict, payload: str) -> dict:
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)

    def _post_recursion_template_req(
        self, url: str, header: dict, limit=1000, offset=0, attempt=1, data_list=None
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

    def _post_template_req(self, url: str, header: dict, payload: str) -> dict | str:
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            message = f"Статус код: {response.status_code} на запрос {url}. Ошибка: {response.text}"
            bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000])
            return message

    def _get_template_req(self, url: str, header: dict) -> dict | str:
        response = requests.request("GET", url, headers=header)
        if response.status_code == 200:
            return json.loads(response.text)
        else:

            message = f"Статус код: {response.status_code} на запрос {url}. Ошибка: {response.text}"
            bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000])
            return message

    def _post_recursion_template_req(
        self, url: str, header: dict, limit=1000, offset=0, attempt=1, data_list=None
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

    def get_auth_header(self, header: dict, perfomance_header: dict) -> dict | str:
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
            message = f"Ошибка при получении токена авторизации к рекламному кабинету. Текст: {data}"
            bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000])
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
        return self.get_proxy_auth_post_request(header, perfomance_header, url, payload)

    def activate_trafarets_top_campaign_req(
        self, header: dict, perfomance_header: dict, campaign_id: str
    ) -> dict:
        """
        Активация кампании
        """
        url = f"{self.main_url}api/client/campaign/{campaign_id}/activate"
        payload = json.dumps({})
        return self.get_proxy_auth_post_request(header, perfomance_header, url, payload)

    def stop_trafarets_top_campaign_req(
        self, header: dict, perfomance_header: dict, campaign_id: str
    ) -> dict:
        """
        Выключить кампанию
        """
        url = f"{self.main_url}api/client/campaign/{campaign_id}/deactivate"
        payload = json.dumps({})
        return self.get_proxy_auth_post_request(header, perfomance_header, url, payload)

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
        return self.get_proxy_auth_post_request(header, perfomance_header, url, payload)

    def add_products_to_search_promo_req(
        self, header: dict, perfomance_header: dict, ozon_sku: str
    ) -> dict:
        """
        Включить продвижение товара в поиске
        """
        url = f"{self.main_url}api/client/search_promo/product/enable"
        payload = json.dumps({"skus": [ozon_sku]})
        return self.get_proxy_auth_post_request(header, perfomance_header, url, payload)

    def campaigns_list_req(self, header: dict, perfomance_header: dict) -> dict:
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
        return self.get_proxy_auth_post_request(header, perfomance_header, url, payload)

    def add_product_to_search_promo_campaign_req(
        self, header: dict, perfomance_header: dict, sku: str
    ) -> dict:
        """
        Добавить артикул в продвижение в поиске
        """
        url = f"{self.main_url}api/client/search_promo/product/enable"
        payload = json.dumps({"skus": [sku]})
        return self.get_proxy_auth_post_request(header, perfomance_header, url, payload)

    def cost_statistic(
        self, header: dict, perfomance_header: dict, date_from: str, date_to: str
    ):
        """
        Статистика расходов рекламных кампаний
        """
        url = f"{self.main_url}api/client/statistics/expense/json?dateFrom={date_from}&dateTo={date_to}"
        return self.get_proxy_auth_get_request(header, perfomance_header, url)
