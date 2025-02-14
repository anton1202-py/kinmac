from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MainInfoViewSet

app_name = "main_response"

router = DefaultRouter()
router.register("articleinfo", MainInfoViewSet, "articleinfo")

urlpatterns = (path("", include(router.urls)),)
