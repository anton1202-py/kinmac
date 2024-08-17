from django.urls import path

from . import views

urlpatterns = [
    path('create', views.create, name='create'),
    path('<int:pk>',
          views.DatabaseDetailView.as_view(),
          name='database_detail'
          ),
    path('<int:pk>/update',
          views.DatabaseUpdateView.as_view(),
          name='database_update'
          ),
    path('<int:pk>/delete',
          views.DatabaseDeleteView.as_view(),
          name='database_delete'
          ),
    path('stock_api/',
          views.database_stock_api,
          name='stock_api'
          ),
    path('stock_api/<str:nm_id>',
          views.DatabaseStockApiDetailView.as_view(),
          name='stock_api_detail'
          ),
    path('stock_api/<int:pk>/delete',
          views.DatabaseStockApiDeleteView.as_view(),
          name='stock_api_delete'
          ),
    path('stock_site/',
          views.stock_site,
          name='stock_site'
          ),
    path('stock_site/<str:nomenclatura_wb>',
          views.DatabaseStockSiteDetailView.as_view(),
          name='stock_site_detail'
          ),
    path('sales/',
          views.database_sales,
          name='sales'
          ),
    path('sales/<str:barcode>',
          views.DatabaseSalesDetailView.as_view(),
          name='sales_detail'
          ),
    path('sales/<int:pk>/delete',
          views.DatabaseSalesDeleteView.as_view(),
          name='sales_delete'
          ),
    path('deliveries/',
          views.database_deliveries,
          name='deliveries'
          ),
    path('orders/',
          views.database_orders,
          name='orders'
          ),
    path('sales_report/',
          views.sales_report,
          name='sales_report'
          ),
    path('weekly_sales/',
          views.weekly_sales_data,
          name='weekly_sales'
          ),
    path('weekly_sales/<str:barcode>',
          views.DatabaseWeeklySalesDetailView.as_view(),
          name='weekly_sales_detail'
          ),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
]