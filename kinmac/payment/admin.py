from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import (ApprovedFunction, Categories, Contractors,
                     PayerOrganization, Payers, PaymentMethod, Payments,
                     Projects, TelegramApproveButtonMessage,
                     TelegramMessageActions)


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
                    'chat_id_tg'
                    )


class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class TelegramApproveButtonMessageAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'approve',
                    'button_name',
                    )


class PayersAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'name',
                    )
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(ApprovedFunction, ApprovedFunctionAdmin)
admin.site.register(TelegramMessageActions, TelegramMessageAdmin)
admin.site.register(TelegramApproveButtonMessage, TelegramApproveButtonMessageAdmin)
admin.site.register(Payers, PayersAdmin)

admin.site.register(Projects)
admin.site.register(Payments)
admin.site.register(Categories)
admin.site.register(Contractors)
#admin.site.register(PaymentMethod)

admin.site.register(PayerOrganization)
#admin.site.register(ApprovedFunction)
