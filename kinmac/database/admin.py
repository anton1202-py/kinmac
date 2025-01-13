from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import CodingMarketplaces, Company


class MarketplaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "english_name")


admin.site.register(CodingMarketplaces, MarketplaceAdmin)
admin.site.register(Company, CompanyAdmin)
