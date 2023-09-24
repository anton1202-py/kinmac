from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('payment_create', views.payment_create, name='payment_create'),
    #path('payment_create', views.PaymentUpdateView.as_view(), name='payment_create'),
    path('payment_statistic', views.payment_statistic, name='payment_statistic'),
    path('<int:pk>/update',
          views.PaymentUpdateView.as_view(),
          name='payment_update'
          ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)