import asyncio
from datetime import datetime
import logging
import tempfile
from openpyxl.styles import Alignment, Border, Side
from django.http import FileResponse, HttpResponse, JsonResponse
from openpyxl import Workbook
import requests
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Case, When, Value, BooleanField, Sum, F
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
import telegram

from database.models import Articles
from google_table.serializers import ActionArticlesSerializer, ProductInfoSerializer
from action.models import ArticleForAction
from kinmac.constants_file import BRAND_LIST


logger = logging.getLogger(__name__)


class ProductInfoViewSet(viewsets.ViewSet):
    """ViewSet для работы с продуктами на платформе Wildberries"""
    # queryset = ProductPrice.objects.filter(platform=Platform.objects.get(platform_type=MarketplaceChoices.MOY_SKLAD))
    queryset = Articles.objects.all()
    serializer_class = ProductInfoSerializer

    def list(self, request):
        """Получение данных о продуктах из API и обновление базы данных"""
        updated_products = Articles.objects.all()
        serializer = ProductInfoSerializer(updated_products, many=True)
        return Response(
            {'articles amount': {len(updated_products)},
             'data': serializer.data},
            status=status.HTTP_200_OK)


class ActionArticleViewSet(viewsets.ViewSet):
    """ViewSet показывает в какой акции участвует артикул и какаяу него целевая цена"""
    queryset = ArticleForAction.objects.all()
    serializer_class = ActionArticlesSerializer

    def list(self, request):
        """Получеине данных а цене артикула в акции"""
        articles_for_actions = ArticleForAction.objects.select_related(
            'action').filter(article__brand__in=BRAND_LIST, action__date_finish__gte=datetime.now())

        # Структура для хранения результата
        result = {}

        for article_for_action in articles_for_actions:
            action_name = article_for_action.action.name

            if action_name not in result:
                result[action_name] = []

            # Используем сериализатор для получения данных
            serializer = ActionArticlesSerializer(article_for_action)
            result[action_name].append(serializer.data)

        return Response(result)
