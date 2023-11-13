import datetime
import json
from datetime import date, timedelta

import pandas as pd
import pytz
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import (ApprovalStatusForm, CashPaymentForm,
                    FilterPayWithCheckingForm, PaymentsForm, PayWithCardForm,
                    PayWithCheckingAccountForm, TransferToCardForm)
from .models import (ApprovalStatus, ApprovedFunction, CashPayment,
                     PayerOrganization, Payments, PayWithCard,
                     PayWithCheckingAccount, TransferToCard)
from .validators import (StripToNumbers, format_phone_number,
                         validate_credit_card)

now_time = datetime.datetime.now()
now = now_time.strftime("%Y-%m-%d %H:%M:%S")


def payment_create(request):

    error = ''
    approval_users = ApprovedFunction.objects.filter(
        rating_for_approval__range=(1, 10)).values_list('id', flat=True)

    approval_users = list(approval_users)

    approvals = {}

    if request.method == 'POST':
        form = PaymentsForm(request.POST)
        form_pay_account = PayWithCheckingAccountForm(
            request.POST, request.FILES)
        form_pay_with_card = PayWithCardForm(request.POST, request.FILES)
        form_transfer_to_card = TransferToCardForm(request.POST)
        form_cash_payment = CashPaymentForm(request.POST)

        if form.is_valid():
            # Заполнение статуса заявки

            payment = Payments(
                creator=f'{request.user.last_name} {request.user.first_name}',
                project=form.cleaned_data['project'],
                category=form.cleaned_data['category'],
                payment_method=form.cleaned_data['payment_method'],
                payment_sum=form.cleaned_data['payment_sum'],
                comment=form.cleaned_data['comment'],
                send_payment_file=form.cleaned_data['send_payment_file'],
                file_of_payment=form.cleaned_data['file_of_payment'],
                urgent_payment=form.cleaned_data['urgent_payment'],
                status_of_payment='На согласовании'
            )
            payment.save()

            raw_users_list = []

            # Алгоритм, который удаляет из согласования юзера, создавшего заявку
            # и всех юзером у которых рейтинг ниже или равен.
            for user_id in approval_users:
                if str(request.user.username) == str(ApprovedFunction.objects.get(id=user_id).username) or ApprovedFunction.objects.get(id=user_id).rating_for_approval <= ApprovedFunction.objects.get(username=request.user.id).rating_for_approval:
                    raw_users_list.append(user_id)
            for del_id in raw_users_list:
                approval_users.remove(del_id)

            for user_id in approval_users:
                if ApprovalStatus.objects.filter(
                        payment=Payments.objects.get(id=payment.pk),
                        user=ApprovedFunction.objects.get(id=user_id)):
                    ApprovalStatus.objects.filter(
                        payment=Payments.objects.get(id=payment.pk),
                        user=ApprovedFunction.objects.get(id=user_id)
                    ).update(status='NOK')
                else:
                    ApprovalStatus(
                        payment=Payments.objects.get(id=payment.pk),
                        user=ApprovedFunction.objects.get(id=user_id),
                        status='NOK').save()
            form = PaymentsForm()
        else:
            error = form.errors
            print(error)

        if request.POST['payment_method'] == '1':
            form_pay_account = PayWithCheckingAccountForm(
                request.POST, request.FILES)
            if form_pay_account.is_valid():
                pay_account = PayWithCheckingAccount(
                    payment_id=Payments.objects.get(id=payment.pk),
                    file_of_bill=form_pay_account.cleaned_data['file_of_bill'],
                )
                pay_account.save()
                error = form.errors
                form_pay_account = PayWithCheckingAccountForm()
            else:
                error1 = form_pay_account.errors
                print(error1)

        elif request.POST['payment_method'] == '2':
            if form_pay_with_card.is_valid():
                pay_with_card = PayWithCard(
                    payment_id=Payments.objects.get(id=payment.pk),
                    link_to_payment=form_pay_with_card.cleaned_data['link_to_payment'],
                )
                pay_with_card.save()
                form_pay_with_card = PayWithCardForm()
            else:
                error2 = form_pay_with_card.errors
                print(error2)

        elif request.POST['payment_method'] == '3':
            if form_transfer_to_card.is_valid():
                transfer_to_card = TransferToCard(
                    payment_id=Payments.objects.get(id=payment.pk),
                    card_number=StripToNumbers(
                        form_transfer_to_card.cleaned_data['card_number']),
                    phone_number=form_transfer_to_card.cleaned_data['phone_number'],
                    payment_receiver=form_transfer_to_card.cleaned_data['payment_receiver'],
                    bank_for_payment=form_transfer_to_card.cleaned_data['bank_for_payment'],
                )
                transfer_to_card.save()
                error = form_transfer_to_card.errors
                print(error)
            else:
                error3 = form_transfer_to_card.errors
                print(error3)

        elif request.POST['payment_method'] == '4':
            if form_cash_payment.is_valid():
                cash_payment = CashPayment(
                    payment_id=Payments.objects.get(id=payment.pk),
                    cash_payment_payment_data=form_cash_payment.cleaned_data[
                        'cash_payment_payment_data']
                )
                cash_payment.save()
                error = form.errors
                form_cash_payment = CashPaymentForm()
            else:
                error4 = form_cash_payment.errors
                print(error4)

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
    return render(request, 'payment/payment_create.html', data)


def approval_person(payment_username):
    approval_users = ApprovedFunction.objects.filter(
        rating_for_approval__range=(0, 10))
    username_rating = {}

    for i in approval_users:
        username_rating[f'{i.username}'] = [
            i.rating_for_approval, f'{i.job_title}', f'{i.first_name} {i.last_name}']
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


def payment_common_statistic(request):
    """Функция отвечает за отображение списка заявок на платёж"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    payments = Payments.objects.all().order_by('id')
    approval_users = ApprovedFunction.objects.filter(
        rating_for_approval__range=(1, 10))

    usernames = [str(user.username) for user in approval_users]
    approval_status = ApprovalStatus.objects.all()

    pay_account = PayWithCheckingAccount.objects.all()
    form = FilterPayWithCheckingForm(request.POST or None)
    main_form = PaymentsForm(request.POST, request.FILES)
    pay_check = PayWithCheckingAccountForm(request.POST, request.FILES)

    datefinish = date.today()
    datestart = date(datefinish.year, datefinish.month, 1)
    amount_sum = payments.aggregate(total_amount=Sum('payment_sum'))[
        'total_amount']

    if request.method == 'POST' and 'approval' in request.POST.keys():
        ApprovalStatus.objects.filter(
            payment=Payments.objects.get(id=request.POST['approval']),
            user=ApprovedFunction.objects.get(
                username=request.user.id)
        ).update(status='OK')
        payments.filter(id=request.POST['approval']).update(
            status_of_payment=f'Согласовано {request.user.last_name} {request.user.first_name}'
        )
        return redirect('payment_common_statistic')

    elif request.method == 'POST' and 'reject_payment' in request.POST.keys():
        ApprovalStatus.objects.filter(
            payment=Payments.objects.get(id=request.POST['reject_payment']),
            user=ApprovedFunction.objects.get(
                username=request.user.id)
        ).update(
            status='REJECTED',
            rejection_reason=request.POST['popup-input-name']
        )

        payments.filter(id=request.POST['reject_payment']).update(
            accountant='',
            date_of_payment=None,
            status_of_payment=f'Отклонено {request.user.last_name} {request.user.first_name}',
            rejection_reason=request.POST['popup-input-name']
        )
        return redirect('payment_common_statistic')

    elif request.method == 'POST' and 'pay_payment' in request.POST.keys():
        pay = Payments.objects.get(id=request.POST['pay_payment'])

        pay.status_of_payment = 'Оплачено'
        pay.date_of_payment = now
        pay.payer_organization = PayerOrganization.objects.get(
            id=request.POST['payer_organization'])

        if str(pay.project) == 'KINMAC' and str(pay.payer_organization) == 'ИП Лисов Юрий Владимирович ИНН 366315065753' and (
           str(pay.payment_method) == 'Оплата по расчетному счету' or str(pay.payment_method) == 'Оплата по карте на сайте'):
            pay.payment_coefficient = 1.02
        if str(pay.project) == 'KINMAC' and (
           str(pay.payment_method) == 'Перевод на карту' or str(pay.payment_method) == 'Наличная оплата'):
            pay.payment_coefficient = 1.02
        pay.contractor_name = request.POST['contractor_name']

        if request.FILES:
            pay.file_of_payment = request.FILES['file_of_payment']
        pay.accountant = f'{request.user.last_name} {request.user.first_name}'
        pay.save()

        return redirect('payment_common_statistic')

    elif request.method == 'POST' and 'delete' in request.POST.keys():
        ApprovalStatus.objects.filter(
            payment=Payments.objects.get(id=request.POST['delete'])).delete()
        payment_for_del = payments.get(id=request.POST['delete'])
        if payment_for_del.payment_method.id == 1:
            payment_for_del.paywithcheckingaccount_set.all().delete()
        elif payment_for_del.payment_method.id == 2:
            payment_for_del.paywithcard_set.all().delete()
        elif payment_for_del.payment_method.id == 3:
            payment_for_del.transfertocard_set.all().delete()
        elif payment_for_del.payment_method.id == 4:
            payment_for_del.cashpayment_set.all().delete()

        payment_for_del.delete()
        return redirect('payment_common_statistic')

    elif request.method == 'POST' and form.is_valid():

        date_filter = form.cleaned_data.get("date_filter")
        payment_type = form.cleaned_data.get("payment_type")
        category = form.cleaned_data.get("category")
        contractor_name = form.cleaned_data.get("contractor_name")
        status_of_payment = form.cleaned_data.get("status_of_payment")

        if date_filter:
            payments = payments.filter(
                Q(pub_date__date=date_filter)).order_by('id')
        if category:
            payments = payments.filter(
                Q(category__name=category)).order_by('id')
        if contractor_name:
            payments = Payments.objects.filter(
                Q(contractor_name=contractor_name)).order_by('id')
        if payment_type:
            payments = payments.filter(
                Q(payment_method=payment_type)).order_by('id')
        if status_of_payment:
            payments = payments.filter(
                Q(status_of_payment__icontains=status_of_payment)
            ).order_by('id')
        amount_sum = payments.aggregate(total_amount=Sum('payment_sum'))[
            'total_amount']

    context = {
        'amount_sum': amount_sum,
        'datestart': datestart,
        'datefinish': datefinish,
        'approval_users': approval_users,
        'approval_status': approval_status,
        'usernames': usernames,
        'form': form,
        'payments': payments,
        'pay_account': pay_account,
        'main_form': main_form,
        'pay_check': pay_check,
    }
    return render(request, 'payment/payment_common_statistic.html', context)


class PaymentDetailView(UpdateView):
    model = Payments
    second_model = PayWithCheckingAccount
    pay_with_card = PayWithCard
    transfer_for_card = TransferToCard
    cash_payment = CashPayment
    approval_model = ApprovalStatus

    form_class = PaymentsForm
    form_class2 = PayWithCheckingAccountForm
    pay_with_card_form = PayWithCardForm
    transfer_for_card_form = TransferToCardForm
    cash_payment_form = CashPaymentForm
    approval_model_form = ApprovalStatusForm

    template_name = 'payment/payment_detail.html'
    context_object_name = 'payments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['approval_model'] = self.approval_model.objects.filter(
            payment=self.object.pk)
        data_update_dict = {
            self.second_model.objects.filter(
                payment_id=self.object.pk): [self.form_class2, 'second_form'],
            self.pay_with_card.objects.filter(
                payment_id=self.object.pk): [self.pay_with_card_form, 'pay_with_card_form'],
            self.transfer_for_card.objects.filter(
                payment_id=self.object.pk): [self.transfer_for_card_form, 'transfer_for_card_form'],
            self.cash_payment.objects.filter(
                payment_id=self.object.pk): [self.cash_payment_form, 'cash_payment_form'],
            self.approval_model.objects.filter(
                payment=self.object.pk): [self.approval_model_form, 'approval_model_form']
        }

        for key, value in data_update_dict.items():
            if key:
                model_data = key[0]
                form_class_data = value[0](instance=model_data)
                context[f'{value[1]}'] = form_class_data
        return context

    def get_queryset(self):
        return Payments.objects.filter(id=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        form.instance = self.object
        return redirect(f'payment_detail', self.object.pk)


class PaymentUpdateView(UpdateView):
    model = Payments
    second_model = PayWithCheckingAccount
    pay_with_card = PayWithCard
    transfer_for_card = TransferToCard
    cash_payment = CashPayment
    approval_model = ApprovalStatus

    form_class = PaymentsForm
    form_class2 = PayWithCheckingAccountForm
    pay_with_card_form = PayWithCardForm
    transfer_for_card_form = TransferToCardForm
    cash_payment_form = CashPaymentForm
    approval_model_form = ApprovalStatusForm

    template_name = 'payment/payment_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.approval_model.objects.filter(
            payment=self.object.pk)[0]

        context['approval_model'] = self.approval_model.objects.filter(
            payment=self.object.pk)
        for i in self.approval_model.objects.filter(
                payment=self.object.pk):
            print(i.user.username, i.status)
        data_update_dict = {
            self.second_model.objects.filter(
                payment_id=self.object.pk): [self.form_class2, 'second_form'],
            self.pay_with_card.objects.filter(
                payment_id=self.object.pk): [self.pay_with_card_form, 'pay_with_card_form'],
            self.transfer_for_card.objects.filter(
                payment_id=self.object.pk): [self.transfer_for_card_form, 'transfer_for_card_form'],
            self.cash_payment.objects.filter(
                payment_id=self.object.pk): [self.cash_payment_form, 'cash_payment_form'],
            self.approval_model.objects.filter(
                payment=self.object.pk): [self.approval_model_form, 'approval_model_form']
        }

        for key, value in data_update_dict.items():
            if key:
                model_data = key[0]
                form_class_data = value[0](instance=model_data)
                context[f'{value[1]}'] = form_class_data

        return context

    def get_object(self, queryset=None):
        obj, created = Payments.objects.get_or_create(pk=self.kwargs['pk'])
        return obj

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        data_update_dict = {
            self.second_model.objects.filter(
                payment_id=self.object.pk): PayWithCheckingAccountForm,
            self.pay_with_card.objects.filter(
                payment_id=self.object.pk): PayWithCardForm,
            self.transfer_for_card.objects.filter(
                payment_id=self.object.pk): TransferToCardForm,
            self.cash_payment.objects.filter(
                payment_id=self.object.pk): CashPayment
        }

        for key, value in data_update_dict.items():
            if key:
                model_data = key[0]
                form_class = value(
                    request.POST, request.FILES, instance=model_data)
                if form.is_valid() and form_class.is_valid():
                    return self.form_valid(form, form_class)
                else:
                    # print(form_class.errors)
                    # messages.error(request, "Error")
                    # print('Формы НЕ валидны')
                    return self.form_invalid(form, form_class)

    def form_valid(self, form, form_2):
        self.object = form.save()
        form_2.save()
        return redirect('payment_common_statistic')

    def form_invalid(self, form, form_2):
        return self.render_to_response(
            self.get_context_data(form=form, form2=form_2)
        )
