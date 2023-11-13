from django.contrib import admin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from .models import (ApprovedFunction, Categories, Contractors,
                     PayerOrganization, Payers, PaymentMethod, Payments,
                     Projects)

admin.site.register(Projects)
admin.site.register(Payments)
admin.site.register(Categories)
admin.site.register(Contractors)
admin.site.register(PaymentMethod)
admin.site.register(Payers)
admin.site.register(PayerOrganization)
admin.site.register(ApprovedFunction)
