from django.contrib import admin

from .models import CityData


class CityDataAdmin(admin.ModelAdmin):
    list_display = ('city_name', 'dest')


admin.site.register(CityData, CityDataAdmin)
