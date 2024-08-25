from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import CodingMarketplaces


class CodingMarketplacesAdmin(admin.ModelAdmin):
    list_display = ('id', 'marketpalce')


admin.site.register(CodingMarketplaces, CodingMarketplacesAdmin)
