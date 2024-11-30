from django.urls import include, path
from rest_framework.routers import DefaultRouter

from google_table.views import ActionArticleViewSet, ResponseWithAllViewSet

router = DefaultRouter()

router.register(r'product-info', ResponseWithAllViewSet,
                basename='product-info')
router.register(r'action-info', ActionArticleViewSet, basename='action-info')


urlpatterns = [
    path('', include(router.urls)),
]
