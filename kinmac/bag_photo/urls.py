from django.urls import path

from .views import bag_photo_view

urlpatterns = [
    path('upload_image/', bag_photo_view, name='upload_image'),
]