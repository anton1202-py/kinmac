from django.urls import path

from . import views

urlpatterns = [
    path('common_sales_analytic', views.common_sales_analytic, name='common_sales_analytic'),
    path('sales_analytic_costprice', views.add_costprice_article, name='sales_analytic_costprice'),
    path('article_sales_analytic/<int:article>',
          views.ArticleAnalyticsDetailView.as_view(),
          name='article_sales_analytic_detail'
          ),
    

    path('update_costprice/', views.update_costprice,
         name='update_costprice'),
]