from django.utils import timezone
from rest_framework import serializers

from database.models import Articles
from action.models import ArticleForAction


class ProductInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articles
        fields = ['id', 'common_article', 'brand', 'barcode', 'nomenclatura_wb',
                  'name']


class ActionArticlesSerializer(serializers.ModelSerializer):
    article = serializers.CharField(source='article.common_article')

    class Meta:
        model = ArticleForAction
        fields = ['article', 'action_price']
