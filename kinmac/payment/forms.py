from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import (CheckboxInput, ChoiceField, FileInput, ModelForm,
                          TextInput)

from .models import (CashPayment, Categories, PayerOrganization, Payers,
                     PaymentMethod, Payments, PayWithCard,
                     PayWithCheckingAccount, Projects, TransforToCard)


class PaymentsForm(ModelForm):
    class Meta:
        model = Payments
        fields = ['project', 'category', 'payment_method', 'payment_sum',
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
        self.fields['payment_method'].empty_label = None


class PayWithCheckingAccountForm(ModelForm):
    class Meta:
        model = PayWithCheckingAccount
        fields = ['payer', 'payer_organization', 'contractor_name',
                  'contractor_bill_number', 'contractor_bik_of_bank',
                  'file_of_bill']
        #payer = forms.ChoiceField(choices=Payers.objects.all())
        #payer_organization = forms.ChoiceField(choices=PayerOrganization.objects.all())
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
        fields = ['payer', 'payer_organization', 'link_to_payment',
                  'comment']
        #payer = forms.ChoiceField(choices=Payers.objects.all())
        #payer_organization = forms.ChoiceField(choices=PayerOrganization.objects.all())
        widgets = {            
            'link_to_payment': TextInput(attrs={
                'class': 'form-control',
            }),
            'comment': TextInput(attrs={
                'class': 'form-control',

            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PayWithCardForm, self).__init__(*args, **kwargs)
        self.fields['payer'].empty_label = None
        self.fields['payer_organization'].empty_label = None


class TransforToCardForm(ModelForm):
    class Meta:
        model = TransforToCard
        fields = ['card_number', 'phone_number', 'payment_receiver',
                  'bank_for_payment']
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
        fields = ['payment_receiver', 'comment_cashpayment']
        widgets = {            
            'payment_receiver': TextInput(attrs={
                'class': 'form-control',
            }),
            'comment_cashpayment': TextInput(attrs={
                'class': 'form-control',
            }),
        }