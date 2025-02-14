from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
    path("database/", include("database.urls")),
    path("payment/", include("payment.urls")),
    path("check_report/", include("check_report.urls")),
    path("bag_photo/", include("bag_photo.urls")),
    path("sales_analytics/", include("sales_analytics.urls")),
    path("position/", include("position.urls")),
    path("api/", include("google_table.urls")),
    path("api/v1/", include("insale.urls", namespace="insale")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
