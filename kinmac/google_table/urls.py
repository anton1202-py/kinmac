from django.urls import include, path
from rest_framework.routers import DefaultRouter

from google_table.views import ActionArticleViewSet, AdvertCostViewSet, ArticleLogisticCostViewSet, MarketplaceCommissionViewSet, ProductInfoViewSet, SppPriceStockDataViewSet

router = DefaultRouter()

router.register(r'product-info', ProductInfoViewSet, basename='product-info')
router.register(r'action-info', ActionArticleViewSet, basename='action-info')
router.register(r'comissions', MarketplaceCommissionViewSet,
                basename='comissions')
router.register(r'logistic-cost', ArticleLogisticCostViewSet,
                basename='logistic-cost')
router.register(r'spp-stock', SppPriceStockDataViewSet,
                basename='spp-stock')
router.register(r'adv-cost', AdvertCostViewSet,
                basename='adv-cost')

urlpatterns = [
    path('', include(router.urls)),
]
