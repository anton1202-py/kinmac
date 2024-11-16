from django.urls import include, path
from rest_framework.routers import DefaultRouter

from google_table.views import ActionArticleViewSet, ProductInfoViewSet

router = DefaultRouter()

router.register(r'product-info', ProductInfoViewSet, basename='product-info')
router.register(r'action-info', ActionArticleViewSet, basename='action-info')


urlpatterns = [
    path('', include(router.urls)),
    # path('profitabilitys/<int:user_id>/',
    #      ProfitabilityAPIView.as_view(), name='profitability-api'),
    # # path('profitability/<int:user_id>/products_by_category/', ProductsByCategoryAPIView.as_view(),
    # #      name='products_by_category'),
    # path('unit_economics/update-price/',
    #      UpdatePriceView.as_view(), name='update-price'),
    # path('calculate-marketplace-price/', CalculateMarketplacePriceView.as_view(),
    #      name='calculate-marketplace-price'),
    # path('marketplace-actions/', MarketplaceActionListView.as_view(),
    #      name='marketplace-actions-list'),
    # path('user-id/', UserIdView.as_view(), name='user-id'),
    # path('topselectors/', TopSelectorsViewSet.as_view(), name='topselectors'),
    # path('calculate-price/', CalculateMPPriceView.as_view(), name='new_price'),
    # path('action-list/', MarketplaceActionList.as_view(), name='actions'),
    # path('product_flag/', UpdateMarketplaceProductFlag.as_view(), name='flag-false'),
]
