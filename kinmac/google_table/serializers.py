from django.utils import timezone
from rest_framework import serializers

from database.models import ArticlePriceStock, Articles
from action.models import ArticleForAction
from unit_economic.models import MarketplaceCommission


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


class MarketplaceCommissionSerializer(serializers.ModelSerializer):
    marketplace_product = serializers.CharField(
        source='marketplace_product.common_article')
    width = serializers.CharField(
        source='marketplace_product.width')
    height = serializers.CharField(
        source='marketplace_product.height')
    length = serializers.CharField(
        source='marketplace_product.length')

    class Meta:
        model = MarketplaceCommission
        fields = ['marketplace_product',
                  'fbo_commission', 'width', 'height', 'length']


class SppPriceStockDataSerializer(serializers.ModelSerializer):
    article = serializers.CharField(
        source='article.common_article')

    class Meta:
        model = ArticlePriceStock
        fields = ['article', 'date', 'common_stock',
                  'price_after_seller_disc', 'spp']
