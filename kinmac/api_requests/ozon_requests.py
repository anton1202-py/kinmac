import json
import requests


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

    def ozon_product_info(self, header: dict, products: list) -> dict:
        url = f"{self.MAIN_URL}v3/product/info/list"
        payload = json.dumps({"offer_id": [], "product_id": products, "sku": []})
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
        self.MAIN_URL = "https://api-seller.ozon.ru/"

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
        url = f"{self.MAIN_URL}v1/cluster/list"
        payload = json.dumps({"cluster_type": "CLUSTER_TYPE_OZON"})
        return self._post_template_req(url, header, payload)

    def warehouse_stock_req(self, header: dict):
        url = f"{self.MAIN_URL}v2/analytics/stock_on_warehouses"
        return self._post_recursion_template_req(url, header)
