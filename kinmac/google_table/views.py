from datetime import datetime
import logging
from rest_framework import status, viewsets
from rest_framework.response import Response

from google_table.serializers import ActionArticlesSerializer
from action.models import ArticleForAction
from kinmac.constants_file import BRAND_LIST
from google_table.logics import WbAnalyticalTableData, WbMarketplaceArticlesData

logger = logging.getLogger(__name__)


class ActionArticleViewSet(viewsets.ViewSet):
    """ViewSet показывает в какой акции участвует артикул и какаяу него целевая цена"""
    queryset = ArticleForAction.objects.all()
    serializer_class = ActionArticlesSerializer

    def list(self, request):
        """Получеине данных а цене артикула в акции"""
        try:
            articles_for_actions = ArticleForAction.objects.select_related(
                'action').filter(article__brand__in=BRAND_LIST, action__date_finish__gte=datetime.now()).order_by('article__common_article')
            result = {}
            for article_for_action in articles_for_actions:
                action_name = article_for_action.action.name
                date_start = article_for_action.action.date_start
                date_finish = article_for_action.action.date_finish

                if action_name not in result:
                    result[action_name] = {
                        'date_start': date_start, 'date_finish': date_finish, 'articles': []}
                serializer = ActionArticlesSerializer(article_for_action)
                result[action_name]['articles'].append(serializer.data)
            return Response(result)
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return Response({'error': f'Произошла ошибка при получении данных.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class TestViewSet(viewsets.ViewSet):
    """Для тестов функций"""

    def list(self, request):
        weeks_amount = int(request.query_params.get('weeks'))
        common_data = WbAnalyticalTableData(weeks_amount)

        return Response(common_data)
