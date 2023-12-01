from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path('payment_create', views.payment_create, name='payment_create'),
    path('payment_common_statistic', views.payment_common_statistic,
         name='payment_common_statistic'),
    path('<int:pk>/detail',
         views.PaymentDetailView.as_view(),
         name='payment_detail'
         ),
    path('<int:pk>/update',
         views.PaymentUpdateView.as_view(),
         name='payment_update'
         ),
     path('login/',
         views.login_by_chat_id,
         name='payment_login'
         ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
