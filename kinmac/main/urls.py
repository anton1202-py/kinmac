from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from database import views


urlpatterns = [
    path('', views.database_home, name='database_home'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)