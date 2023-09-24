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