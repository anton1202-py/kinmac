import logging

from rest_framework import viewsets
from rest_framework.response import Response

from google_table.logics import WbMarketplaceArticlesData

logger = logging.getLogger(__name__)


class ResponseWithAllViewSet(viewsets.ViewSet):
    """Отдает расходы рекламы на каждую продажу."""

    def list(self, request):
        weeks_amount = int(request.query_params.get('weeks'))
        common_data = WbMarketplaceArticlesData(weeks_amount)

        comission_data = common_data.comission_data()
        spp_data = common_data.spp_stock_data()
        advert_info = common_data.advert_data()
        log_stor_data = common_data.logistic_storage_cost()

        for article, data in comission_data.items():
            data.update(spp_data[article])
            data.update(advert_info[article])
            data.update(log_stor_data[article])
        return Response(comission_data)
