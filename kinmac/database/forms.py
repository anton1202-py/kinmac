from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import CharField, ModelForm, PasswordInput, TextInput

from .models import Articles


class ArticlesForm(ModelForm):
    class Meta:
        model = Articles
        fields = ['common_article', 'brend', 'barcode', 'nomenclatura_wb',
                  'nomenclatura_ozon', 'predmet', 'size', 'model',
                  'color', 'prime_cost', 'average_cost']
        widgets = {
            'common_article': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул'
            }),
            'brend': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Бренд'
            }),
            'barcode': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод'
            }),
            'nomenclatura_wb': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номенклатура WB'
            }),
            'nomenclatura_ozon': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номенклатура OZON'
            }),
            'predmet': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Предмет'
            }),
            'size': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Размер'
            }),
            'model': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Модель'
            }),
            'color': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Цвет'
            }),
            'prime_cost': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Себестоимость'
            }),
            'average_cost': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Средняя себестоимость'
            })
        }


class LoginUserForm(AuthenticationForm):
    username = CharField(
        label='Логин',
        widget=TextInput(attrs={'class': 'form-control'})
    )
    password = CharField(
        label='Пароль',
        widget=PasswordInput(attrs={'class': 'form-control'})
    )


class SelectDateForm(forms.Form):
    datestart = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    datefinish = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    article_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))


class SelectDateStocksForm(forms.Form):
    datestart = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    datefinish = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    article_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    stock_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))


class SelectArticlesForm(forms.Form):
    article_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
