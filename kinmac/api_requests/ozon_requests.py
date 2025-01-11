import json
import requests


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
