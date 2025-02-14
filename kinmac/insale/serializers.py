from datetime import datetime
from database.models import (
    ArticlePriceStock,
    Articles,
    Company,
    OzonProduct,
    WarehouseBalance,
)
from django.db.models import Sum, Max
from rest_framework import serializers


class OzonArticlesInfoSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    ozon_sku = serializers.SerializerMethodField()

    class Meta:
        model = OzonProduct
        fields = ("ozon_sku", "price", "stock")

    def get_ozon_sku(self, obj):
        ozon_sku = obj.sku
        return ozon_sku

    def get_stock(self, obj):
        stock = 0
        date = datetime.now().date()
        stock_data = (
            WarehouseBalance.objects.filter(
                company=Company.objects.filter(name="KINMAC").first(),
                ozon_article=obj,
                date=date,
            )
            .values("ozon_article__sku")
            .annotate(
                common_stock=Sum("quantity"),
            )
        )
        if stock_data:
            stock = stock_data[0]["common_stock"]

        return stock

    def get_price(self, obj):
        price = obj.marketing_price
        return int(float(price))


class WildberriesArticlesInfoSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    wb_nm_id = serializers.SerializerMethodField()

    class Meta:
        model = Articles
        fields = ("wb_nm_id", "price", "stock")

    def get_wb_nm_id(self, obj):
        wb_nm_id = obj.nomenclatura_wb
        return wb_nm_id

    def get_stock(self, obj):
        stock = 0
        date = datetime.now().date()
        stock_data = ArticlePriceStock.objects.filter(
            article=obj, date=date
        ).first()
        if stock_data:
            stock = stock_data.common_stock
        return stock

    def get_price(self, obj):
        price = (
            ArticlePriceStock.objects.filter(article=obj)
            .order_by("-date")
            .first()
            .price_in_page
        )
        return int(price)


class OzonInfoSerializer(serializers.Serializer):
    product_list = OzonArticlesInfoSerializer(many=True)

    class Meta:
        fields = ["product_list"]


class MainInfoSerializer(serializers.Serializer):
    wb_nm_id = WildberriesArticlesInfoSerializer(many=True)
    ozon_product_list = OzonArticlesInfoSerializer(many=True)

    class Meta:
        fields = ["wb_nm_id", "ozon_product_list"]
