from datetime import date, timedelta
import datetime
import pandas as pd

from django.contrib import messages 
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect, render
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, CreateView, UpdateView

from .forms import PaymentsForm, PayWithCardForm, PayWithCheckingAccountForm, TransferToCardForm, CashPaymentForm
from .models import Payments, PayWithCheckingAccount, PayWithCard, TransferToCard, CashPayment, ApprovedFunction


now_time = datetime.datetime.now()
now = now_time.strftime("%Y-%m-%d %H:%M:%S")

def payment_create(request):

    obj = approval_person(request.user.username)
    print(obj)
    
    error = ''
    now_time = datetime.datetime.now()
    now = now_time.strftime("%Y-%m-%d %H:%M:%S")
    if request.method == 'POST':
        form = PaymentsForm(request.POST)
        form_pay_account = PayWithCheckingAccountForm(request.POST, request.FILES)
        form_pay_with_card = PayWithCardForm(request.POST, request.FILES)
        form_transfer_to_card = TransferToCardForm(request.POST)
        form_cash_payment = CashPaymentForm(request.POST)
        if form.is_valid():
            payment = Payments(
                    creator=request.user.username,
                    project=form.cleaned_data['project'],
                    category=form.cleaned_data['category'],
                    payment_method=form.cleaned_data['payment_method'],
                    payment_sum=form.cleaned_data['payment_sum'],
                    comment=form.cleaned_data['comment'], 
                    send_payment_file=form.cleaned_data['send_payment_file'],
                    file_of_payment=form.cleaned_data['file_of_payment'],
                    urgent_payment=form.cleaned_data['urgent_payment']
                    )
            payment.save()
            saved_payment=Payments.objects.get(id=payment.pk)
            saved_payment.status_of_payment = approval_person(request.user.username)
            saved_payment.save(update_fields=["status_of_payment"])

            form = PaymentsForm()

        if request.POST['payment_method'] == '1':
            form_pay_account = PayWithCheckingAccountForm(request.POST, request.FILES)
            if form_pay_account.is_valid():
                pay_account = PayWithCheckingAccount(
                    payment_id=Payments.objects.get(id=payment.pk),
                    payer=form_pay_account.cleaned_data['payer'],
                    payer_organization=form_pay_account.cleaned_data['payer_organization'],
                    contractor_name=form_pay_account.cleaned_data['contractor_name'],
                    contractor_bill_number=form_pay_account.cleaned_data['contractor_bill_number'],
                    contractor_bik_of_bank=form_pay_account.cleaned_data['contractor_bik_of_bank'],
                    file_of_bill=form_pay_account.cleaned_data['file_of_bill'],
                )
                pay_account.save()
                error = form.errors
                print('Должно сохраниться главная + form_pay_account')
                form_pay_account = PayWithCheckingAccountForm()

        elif request.POST['payment_method'] == '2':
            if form_pay_with_card.is_valid():
                pay_with_card = PayWithCard(
                    payment_id=Payments.objects.get(id=payment.pk),
                    payer=form_pay_with_card.cleaned_data['payer'],
                    with_card_payer_organization=form_pay_with_card.cleaned_data['with_card_payer_organization'],
                    link_to_payment=form_pay_with_card.cleaned_data['link_to_payment'],
                )
                pay_with_card.save()
                error = form.errors
                form_pay_with_card = PayWithCardForm()
                print('Должно сохраниться главная + form_pay_with_card')
            
        elif request.POST['payment_method'] == '3':
            if form_transfer_to_card.is_valid():
                transfer_to_card = TransferToCard(
                    payment_id=Payments.objects.get(id=payment.pk),
                    card_number=form_transfer_to_card.cleaned_data['card_number'],
                    phone_number=form_transfer_to_card.cleaned_data['phone_number'],
                    payment_receiver=form_transfer_to_card.cleaned_data['payment_receiver'],
                    bank_for_payment=form_transfer_to_card.cleaned_data['bank_for_payment'],
                )
                transfer_to_card.save()
                error = form.errors
                form_transfer_to_card = TransferToCardForm()
                print('Должно сохраниться главная + form_transfer_to_card')

        elif request.POST['payment_method'] == '4':
            if form_cash_payment.is_valid():
                cash_payment = CashPayment(
                    payment_id=Payments.objects.get(id=payment.pk),
                    cash_payment_payment_receiver = form_cash_payment.cleaned_data['cash_payment_payment_receiver']
                )
                cash_payment.save()
                error = form.errors
                form_cash_payment = CashPaymentForm()
                print('Должно сохраниться главная + form_cash_payment')
        else:
            print('Форма не сохранилась')
    else:
        form = PaymentsForm()
        form_pay_account = PayWithCheckingAccountForm()
        form_pay_with_card = PayWithCardForm()
        form_transfer_to_card = TransferToCardForm()
        form_cash_payment = CashPaymentForm()
    
    data = {
        'form': form,
        'error': error,
        'form_pay_account': form_pay_account,
        'form_pay_with_card': form_pay_with_card,
        'form_transfer_to_card': form_transfer_to_card,
        'form_cash_payment': form_cash_payment
    }
    return render( request, 'payment/payment_create.html', data)

def approval_person(payment_username):
    approval_users = ApprovedFunction.objects.filter(rating_for_approval__range=(0, 10))
    username_rating = {}
    
    for i in approval_users:
        username_rating[f'{i.username}'] = [i.rating_for_approval, f'{i.job_title}', f'{i.first_name} {i.last_name}']
    user_rating = username_rating[payment_username][0]
    if username_rating[payment_username][0] == 0 and username_rating[payment_username][1] != 'Бухгалтер':
        for lst in username_rating.values():
            if lst[0] == 1:
                return f"На согласовании у {lst[2]}"
    elif username_rating[payment_username][0] > 0 and username_rating[payment_username][0] < 10:
        for lst in username_rating.values():
            if lst[0] > user_rating:
                return f"На согласовании у {lst[2]}"
    elif username_rating[payment_username][0] == 10:
        for lst in username_rating.values():
            return f"На оплате у бухгалтера"


def payment_statistic_pay_account(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    payments = Payments.objects.all().order_by('id')
    pay_account = PayWithCheckingAccount.objects.all()
    context = {
        'payments': payments,
        'pay_account': pay_account,
        }
    return render(request, 'payment/payment_statistic_pay_account.html', context)


def payment_statistic_pay_card(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    payments = Payments.objects.all().order_by('id')
    pay_with_card = PayWithCard.objects.all()
    context = {
        'payments': payments,
        'pay_with_card': pay_with_card,
        }
    return render(request, 'payment/payment_statistic_pay_card.html', context)

def payment_statistic_transfer_card(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    payments = Payments.objects.all().order_by('id')
    transfer_to_card = TransferToCard.objects.all()
    context = {
        'payments': payments,
        'transfer_to_card': transfer_to_card,
        }
    return render(request, 'payment/payment_statistic_transfer_card.html', context)


def payment_statistic_pay_cash(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    payments = Payments.objects.all().order_by('id')
    cash_payment = CashPayment.objects.all()
    context = {
        'payments': payments,
        'cash_payment': cash_payment
        }
    return render(request, 'payment/payment_statistic_pay_cash.html', context)


class PaymentDetailView(DetailView):
    model = Payments
    form_class = PaymentsForm
    form_class2 = PayWithCheckingAccountForm
    second_model = PayWithCheckingAccount
    template_name = 'payment/payment_detail_pay_account.html'
    context_object_name = 'payments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['second_model_data'] = self.second_model.objects.filter(payment_id=self.object.pk)[0]
        return context

    def get_queryset(self):
        return Payments.objects.filter(id=self.kwargs['pk'])
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        saved_payment=Payments.objects.get(id=self.object.pk)
        user = User.objects.get(username=request.user.username)
        groups = user.groups.all()
        if request.method == 'POST':
            if 'pay_payment' in request.POST:
                saved_payment.status_of_payment =f'Оплачено {request.user.username}'
                saved_payment.accountant = request.user.username
                saved_payment.date_of_payment = now
                saved_payment.save(update_fields=['accountant', 'date_of_payment', 'status_of_payment'])
            elif 'cancel_payment' in request.POST:
                saved_payment.status_of_payment =f'Отменена {request.user.username}'
                saved_payment.accountant = None
                saved_payment.date_of_payment = None
                saved_payment.save(update_fields=['accountant', 'date_of_payment', 'status_of_payment'])
            elif 'approve_payment' in request.POST:
                saved_payment.status_of_payment = approval_person(request.user.username)
                saved_payment.save(update_fields=['status_of_payment'])
            elif 'reject_payment' in request.POST:
                print(request.POST['popup-input-name'])
                saved_payment.rejection_reason = request.POST['popup-input-name']
                saved_payment.status_of_payment =f'Отклонено {request.user.username}'
                saved_payment.save(update_fields=['status_of_payment', 'rejection_reason'])
        
        if request.method == 'GET':
            print(request.GET)

        return redirect(f'payment_detail', self.object.pk)






class PaymentUpdateView(UpdateView):
    model = Payments
    form_class = PaymentsForm
    form_class2 = PayWithCheckingAccountForm
    second_model = PayWithCheckingAccount
    template_name = 'payment/payment_update_account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        second_model_data = self.second_model.objects.filter(payment_id=self.object.pk)[0]
        form_class2_data = self.form_class2(instance=second_model_data)
        context['second_form'] = form_class2_data
        #print(context['second_form'])
        return context

    def get_object(self, queryset=None):
        obj, created = Payments.objects.get_or_create(pk=self.kwargs['pk'])
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        second_model_data = self.second_model.objects.filter(payment_id=self.object.pk)[0]
        form_class2 = PayWithCheckingAccountForm(request.POST, request.FILES, instance=second_model_data)
        
        if form.is_valid() and form_class2.is_valid():
            return self.form_valid(form, form_class2)
        else:
            print(form_class2.errors)
            messages.error(request, "Error")
            print('Формы НЕ валидны')
            return self.form_invalid(form, form_class2)

    def form_valid(self, form, form_class2):
        print('до сохранения форм)')
        self.object = form.save()
        print('первую сохранил')
        form_class2.save()
        print('вторую сохранил')
        return redirect('payment_statistic_pay_account')

    def form_invalid(self, form, form_class2):
        return self.render_to_response(
            self.get_context_data(form=form, form2=form_class2)
        )

