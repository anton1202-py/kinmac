from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
      path('payment_create', views.payment_create, name='payment_create'),
      path('payment_statistic_pay_account', views.payment_statistic_pay_account, name='payment_statistic_pay_account'),
      path('payment_statistic_pay_card', views.payment_statistic_pay_card, name='payment_statistic_pay_card'),
      path('payment_statistic_transfer_card', views.payment_statistic_transfer_card, name='payment_statistic_transfer_card'),
      path('payment_statistic_pay_cash', views.payment_statistic_pay_cash, name='payment_statistic_pay_cash'),

      path('<int:pk>/detail',
            views.PaymentDetailView.as_view(),
            name='payment_detail'
            ),
      path('<int:pk>/update',
            views.PaymentUpdateView.as_view(),
            name='payment_update'
            ),

      path('<int:pk>/pay_card_detail',
          views.PayCardDetailView.as_view(),
          name='pay_card_detail'
          ),
      path('<int:pk>/pay_card_update',
            views.PayCardUpdateView.as_view(),
            name='pay_card_update'
            ),

      path('<int:pk>/transfer_card_detail',
          views.TransferCardDetailView.as_view(),
          name='transfer_card_detail'
          ),
      path('<int:pk>/transfer_card_update',
            views.TransferCardUpdateView.as_view(),
            name='transfer_card_update'
            ),
      
      path('<int:pk>/pay_cash_detail',
          views.PayCashDetailView.as_view(),
          name='pay_cash_detail'
          ),
      path('<int:pk>/pay_cash_update',
            views.PayCashUpdateView.as_view(),
            name='pay_cash_update'
            ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)