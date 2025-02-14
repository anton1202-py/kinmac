from django.http import JsonResponse
from database.models import Articles, OzonProduct
from rest_framework import viewsets

from .serializers import MainInfoSerializer


class MainInfoViewSet(viewsets.ViewSet):
    """Вьюсет для отображения информации об артикулах с Озон и ВБ в виде:
    {
        "wb_nm_id": [
            {
                "wb_nm_id": wb_nm_id,
                "price": price,
                "stock": stock
            }
        ],
        "ozon_product_list": [
            {
                "ozon_sku": ozon_sku,
                "price": price,
                "stock": stock
            }
        ]
    }
    """

    def list(self, request):
        ozon_articles = request.query_params.get("ozon_sku")
        wb_articles = request.query_params.get("wb_nm")
        wb_info = []
        ozon_info = []
        if "wb_nm" in request.query_params:
            wb_article_list = wb_articles.split(",")
            wb_info = Articles.objects.filter(
                nomenclatura_wb__in=wb_article_list
            )
        if "ozon_sku" in request.query_params:
            ozon_article_list = ozon_articles.split(",")
            ozon_info = OzonProduct.objects.filter(sku__in=ozon_article_list)
        serializer = MainInfoSerializer(
            {"wb_nm_id": wb_info, "ozon_product_list": ozon_info}
        )
        return JsonResponse(serializer.data)
