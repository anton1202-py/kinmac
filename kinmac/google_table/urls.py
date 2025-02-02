from django.urls import include, path
from rest_framework.routers import DefaultRouter

from google_table.views import (
    ActionArticleViewSet,
    OzonActionArticleViewSet,
    OzonCommonDataViewSet,
    ResponseWithAllViewSet,
    TestViewSet,
)

router = DefaultRouter()

router.register(
    r"product-info", ResponseWithAllViewSet, basename="product-info"
)
router.register(r"action-info", ActionArticleViewSet, basename="action-info")
router.register(
    r"ozon-product-info", OzonCommonDataViewSet, basename="ozon-product-info"
)
router.register(
    r"ozon-action-info", OzonActionArticleViewSet, basename="ozon-action-info"
)
router.register(r"test-info", TestViewSet, basename="test-info")


urlpatterns = [
    path("", include(router.urls)),
]
