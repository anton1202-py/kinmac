from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import CodingMarketplaces, Company


class CodingMarketplacesAdmin(admin.ModelAdmin):
    list_display = ("id", "marketpalce")


class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "english_name")


admin.site.register(CodingMarketplaces, CodingMarketplacesAdmin)
admin.site.register(Company, CompanyAdmin)
