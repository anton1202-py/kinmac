from datetime import date, timedelta

import pandas as pd
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, CreateView, UpdateView

from .forms import PaymentsForm
from .models import Payments


'''
def payment_create(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    
    form = PaymentsForm(request.POST or None)
    
    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = StocksApi.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        else:
            data = StocksApi.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter))
    context = {
        'form': form,
        'data': data,
        'datestart': str(datestart),
        'articles': articles.all().values(),
    }
    return render(request, 'database/stock_api.html', context)
'''

def payment_create(request):
    error = ''
    if request.method == 'POST':
        form = form = PaymentsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            print('Должно сохраниться')
            #return redirect('payment_create')
        else:
            print('Не сохранилось')
    else:
        form = PaymentsForm()
    data = {
        'form': form,
        'error': error
    }
    return render( request, 'payment/payment_create.html', data)


def payment_statistic(request):

    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    if request.user.is_staff == True:
        data = Payments.objects.all()
        context = {
            'data': data,
        }
    return render( request, 'payment/payment_statistic.html', context)


class PaymentDetailView(DetailView):
    model = Payments
    template_name = 'payment/payment_detail.html'
    context_object_name = 'payment'


class PaymentUpdateView(UpdateView):
    model = Payments
    template_name = 'payment/payment_create.html'
    form_class = PaymentsForm