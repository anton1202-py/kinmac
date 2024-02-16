
from django import forms
from django.forms import (CheckboxInput, ChoiceField, FileInput, ModelForm,
                          NumberInput, Select, TextInput)

from .models import (ApprovalStatus, CashPayment, Categories, Contractors,
                     PayerOrganization, Payers, PaymentMethod, Payments,
                     PayWithCard, PayWithCheckingAccount, Projects,
                     TransferToCard)
from .validators import StripToNumbers, format_phone_number


class PaymentsForm(ModelForm):
    class Meta:
        model = Payments
        fields = ['creator', 'project', 'payer_organization', 'category', 'payment_method', 'payment_sum',
                  'comment', 'send_payment_file', 'contractor_name', 'file_of_payment', 'accountant',
                  'urgent_payment', 'status_of_payment', 'date_of_payment', 'accountant', 'file_of_payment', 'payment_coefficient']
        project = forms.ChoiceField(choices=Projects.objects.all())
        category = forms.ChoiceField(choices=Categories.objects.all())
        # contractor_name = forms.ChoiceField(
        #    choices=Contractors.objects.all(), required=False)
        payer_organization = forms.ChoiceField(
            choices=PayerOrganization.objects.all())

        payment_method = forms.ChoiceField(choices=PaymentMethod.objects.all())
        send_payment_file = forms.CheckboxSelectMultiple()
        urgent_payment = forms.CheckboxSelectMultiple()
        payment_coefficient = forms.FloatField(required=False)
        widgets = {
            'project': Select(attrs={
                'class': 'input-field',
            }),
            'category': Select(attrs={
                'class': 'input-field',
            }),
            'payer_organization': Select(attrs={
                'class': 'input-field',
            }),
            'payment_sum': NumberInput(attrs={
                'class': 'input-field',
            }),
            'contractor_name': Select(attrs={
                'class': 'input-field',
            }),
            'urgent_payment': CheckboxInput(attrs={
                'class': 'input-field',
            }),
            'send_payment_file': CheckboxInput(attrs={
                'class': 'input-field',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'input-field',
            }),
            'payment_method': Select(attrs={
                'class': 'input-field',
            }),
            'file_of_payment': FileInput(attrs={
                'class': 'input-file',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PaymentsForm, self).__init__(*args, **kwargs)
        self.fields['project'].empty_label = None
        self.fields['category'].empty_label = None
        self.fields['payment_method'].empty_label = 'Выбрать'


class PayWithCheckingAccountForm(ModelForm):
    class Meta:
        model = PayWithCheckingAccount
        fields = ['contractor_bill_number', 'contractor_bik_of_bank',
                  'file_of_bill']
        fields_required = ['contractor_name',
                           'contractor_bill_number', 'contractor_bik_of_bank']

        send_payment_file = forms.CheckboxSelectMultiple()
        widgets = {
            'contractor_bill_number': TextInput(attrs={
                'class': 'input-field',

            }),
            'contractor_bik_of_bank': TextInput(attrs={
                'class': 'input-field',

            }),
            'file_of_bill': FileInput(attrs={
                'class': 'input-file',

            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PayWithCheckingAccountForm, self).__init__(*args, **kwargs)


class PayWithCardForm(ModelForm):
    class Meta:
        model = PayWithCard
        fields = ['link_to_payment']
        widgets = {
            'link_to_payment': TextInput(attrs={
                'class': 'input-field',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PayWithCardForm, self).__init__(*args, **kwargs)


class TransferToCardForm(ModelForm):

    class Meta:
        model = TransferToCard
        card_number = forms.IntegerField(
            validators=[StripToNumbers],
            required=False,)
        phone_number = forms.CharField(required=False,)

        fields = ['card_number', 'phone_number', 'payment_receiver',
                  'bank_for_payment']
        fields_required = ['phone_number',
                           'bank_for_payment', 'bank_for_payment']
        widgets = {
            'card_number': TextInput(attrs={
                'class': 'input-field',
            }),
            'phone_number': TextInput(attrs={
                'class': 'input-fieldl',
            }),
            'payment_receiver': TextInput(attrs={
                'class': 'input-field',
            }),
            'bank_for_payment': TextInput(attrs={
                'class': 'input-field',
            }),
        }

        def clean_phone_number(self):
            phone_number = self.cleaned_data.get('phone_number')
            return format_phone_number(phone_number)


class CashPaymentForm(ModelForm):
    class Meta:
        model = CashPayment
        fields = ['cash_payment_payment_data']
        widgets = {
            'cash_payment_payment_data': forms.Textarea(attrs={
                'class': 'input-field',
            }),
        }


class ApprovalStatusForm(ModelForm):
    class Meta:
        model = ApprovalStatus
        fields = ['user', 'status']


class FilterPayWithCheckingForm(forms.Form):
    """Форма отвечает за фильтрацию записей на странице со списком заявок"""
    date_filter = forms.DateField(
        input_formats=['%Y-%m-%d'],
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    payment_type = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.all(),
        required=False,)
    category = forms.ModelChoiceField(
        queryset=Categories.objects.all(),
        required=False,)
    contractor_name = forms.ModelChoiceField(
        queryset=Contractors.objects.all(),
        required=False,)
    status_of_payment = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('Согласовано', 'Согласовано'),
            ('На согласовании', 'На согласовании'),
            ('Оплачено', 'Оплачено'),
            ('Отклонено', 'Отклонено')
        ],
        required=False,)
