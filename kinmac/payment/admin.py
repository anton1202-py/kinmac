from django.contrib import admin

from .models import (ApprovedFunction, Categories, Contractors,
                     PayerOrganization, Payers, PaymentMethod, Payments,
                     Projects, TelegramMessageActions)


class TelegramMessageAdmin(admin.ModelAdmin):
    list_display = ('payment', 'chat_id', 'message_id', 'message_type', 'message_author')


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('id', 'method_name')

class ApprovedFunctionAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'username',
                    'user_name',
                    'first_name',
                    'last_name',
                    'job_title',
                    'rating_for_approval',
                    'chat_id_tg')

admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(ApprovedFunction, ApprovedFunctionAdmin)
admin.site.register(TelegramMessageActions, TelegramMessageAdmin)

admin.site.register(Projects)
admin.site.register(Payments)
admin.site.register(Categories)
admin.site.register(Contractors)
#admin.site.register(PaymentMethod)
admin.site.register(Payers)
admin.site.register(PayerOrganization)
#admin.site.register(ApprovedFunction)
