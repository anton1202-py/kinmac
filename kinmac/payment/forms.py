from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import (CheckboxInput, ChoiceField, FileInput, ModelForm,
                          TextInput)

from .models import (CashPayment, Categories, PayerOrganization, Payers,
                     PaymentMethod, Payments, PayWithCard,
                     PayWithCheckingAccount, Projects, TransferToCard)


class PaymentsForm(ModelForm):
    class Meta:
        model = Payments
        fields = ['creator', 'project', 'category', 'payment_method', 'payment_sum',
                  'comment', 'send_payment_file', 'file_of_payment',
                  'urgent_payment']
        #project = forms.ChoiceField(choices=Projects.objects.all())
        #category = forms.ChoiceField(choices=Categories.objects.all())
        #payment_method = forms.ChoiceField(choices=PaymentMethod.objects.all())
    
        send_payment_file = forms.CheckboxSelectMultiple()
        urgent_payment = forms.CheckboxSelectMultiple()
        widgets = {            
            'payment_sum': TextInput(attrs={
                'class': 'form-control',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
            }),
            'file_of_payment': FileInput(attrs={
                'class': 'form-control',
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
        fields = ['payer', 'payer_organization', 'contractor_name',
                  'contractor_bill_number', 'contractor_bik_of_bank',
                  'file_of_bill']
        fields_required = ['payer', 'payer_organization', 'contractor_name',
                  'contractor_bill_number', 'contractor_bik_of_bank']

        #payer = forms.ChoiceField(
        #    choices=Payers.objects.all(),
        #)
        #payer_organization = forms.ChoiceField(
        #    choices=PayerOrganization.objects.all(),
        #)
        send_payment_file = forms.CheckboxSelectMultiple()
        widgets = {            
            'contractor_name': TextInput(attrs={
                'class': 'form-control',

            }),
            'contractor_bill_number': TextInput(attrs={
                'class': 'form-control',

            }),
            'contractor_bik_of_bank': TextInput(attrs={
                'class': 'form-control',

            }),
            'file_of_bill': FileInput(attrs={
                'class': 'form-control',

            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PayWithCheckingAccountForm, self).__init__(*args, **kwargs)
        self.fields['payer'].empty_label = None
        self.fields['payer_organization'].empty_label = None


class PayWithCardForm(ModelForm):
    class Meta:
        model = PayWithCard
        fields = ['payer', 'with_card_payer_organization', 'link_to_payment']
        #payer = forms.ChoiceField(choices=Payers.objects.all())
        #with_card_payer_organization = forms.ChoiceField(choices=PayerOrganization.objects.all())
        widgets = {            
            'link_to_payment': TextInput(attrs={
                'class': 'form-control',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PayWithCardForm, self).__init__(*args, **kwargs)
        self.fields['payer'].empty_label = None
        self.fields['with_card_payer_organization'].empty_label = None


class TransferToCardForm(ModelForm):
    class Meta:
        model = TransferToCard
        fields = ['card_number', 'phone_number', 'payment_receiver',
                  'bank_for_payment']
        fields_required = ['phone_number', 'bank_for_payment', 'bank_for_payment']
        widgets = {            
            'card_number': TextInput(attrs={
                'class': 'form-control',
            }),
            'phone_number': TextInput(attrs={
                'class': 'form-control',
            }),
            'payment_receiver': TextInput(attrs={
                'class': 'form-control',
            }),
            'bank_for_payment': TextInput(attrs={
                'class': 'form-control',
            }),
        }


class CashPaymentForm(ModelForm):
    class Meta:
        model = CashPayment
        fields = ['cash_payment_payment_receiver']
        widgets = {            
            'cash_payment_payment_receiver': TextInput(attrs={
                'class': 'form-control',
            }),
        }


class FilterPayWithCheckingForm(forms.Form):
    datestart = forms.DateField(
        input_formats=['%Y-%m-%d'],
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    datefinish = forms.DateField(
        input_formats=['%Y-%m-%d'],
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    creator = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    project = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    payer = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    payer_organization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    contractor_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    payment_sum = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    status_of_payment = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))