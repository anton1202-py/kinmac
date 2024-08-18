import datetime
import os
from datetime import date, datetime, timedelta

import telegram
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import UpdateView
from dotenv import load_dotenv
from telegram_working.assistance import (save_message_function,
                                         upgrade_message_function)
from telegram_working.start_tg_approve import start_tg_working

from .forms import (ApprovalStatusForm, CashPaymentForm,
                    FilterPayWithCheckingForm, PaymentsForm, PayWithCardForm,
                    PayWithCheckingAccountForm, TransferToCardForm)
from .models import (ApprovalStatus, ApprovedFunction, CashPayment,
                     Contractors, PayerOrganization, Payments, PayWithCard,
                     PayWithCheckingAccount, TelegramApproveButtonMessage,
                     TelegramMessageActions, TransferToCard)
from .supplement import excel_creating_mod

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def payment_create(request):
    from telegram_working.start_tg_approve import send_message_to_creator
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
            if request.POST['contractor_name']:
                contractor_name_data = Contractors.objects.get(
                    id=request.POST['contractor_name']).name
            elif request.POST['contractor_name_new']:
                contractor_name_data = request.POST['contractor_name_new']

            if request.POST['contractor_name_new']:
                if Contractors.objects.filter(
                        name=request.POST['contractor_name_new']):
                    Contractors.objects.filter(
                        name=request.POST['contractor_name_new']).update()
                else:
                    contractor = Contractors(
                        name=request.POST['contractor_name_new']
                    )
                    contractor.save()

            payment = Payments(
                creator=f'{request.user.last_name} {request.user.first_name}',
                project=form.cleaned_data['project'],
                category=form.cleaned_data['category'],
                payment_method=form.cleaned_data['payment_method'],
                payment_sum=form.cleaned_data['payment_sum'],
                contractor_name=Contractors.objects.get(
                        name=contractor_name_data),
                comment=form.cleaned_data['comment'],
                send_payment_file=form.cleaned_data['send_payment_file'],
                file_of_payment=form.cleaned_data['file_of_payment'],
                urgent_payment=form.cleaned_data['urgent_payment'],
                status_of_payment='На согласовании'
            )
            payment.save()

            if request.POST['contractor_name_new']:
                if Contractors.objects.get(
                        name=request.POST['contractor_name_new']):
                    Contractors.objects.filter(
                        name=request.POST['contractor_name_new']).update()
                else:
                    contractor = Contractors(
                        name=request.POST['contractor_name_new']
                    )
                    contractor.save()
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
                error = form_transfer_to_card.errors
                form_transfer_to_card = TransferToCardForm()
            else:
                error3 = form_transfer_to_card.errors

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
        rating = (ApprovedFunction.objects.get(
            username=request.user.id).rating_for_approval)
        job_title = ApprovedFunction.objects.get(
            username=request.user.id).job_title
        # ApprovedFunction.objects.get(username)
        send_message_to_creator(payment.pk, request.user.username, rating)
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


def get_button_value(request):
    """
    Отдает данные JQUERY когда вызывается форма написания комментария
    при согласовании заявки.
    """
    approve_user = ApprovedFunction.objects.get(
        username = request.user.id
    )
    buttons = TelegramApproveButtonMessage.objects.get(
        approve=approve_user.pk
    )
    button_value = buttons.button_name
    return JsonResponse({'button': button_value})


def payment_common_statistic(request):
    """Функция отвечает за отображение списка заявок на платёж"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    time_filter = datetime.now() - timedelta(days=60)
    payments = Payments.objects.filter(pub_date__gte=time_filter).order_by('id')
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

    #if request.method == 'POST' and 'approval' in request.POST.keys():
    if request.method == 'POST' and 'approval' in request.POST.keys():
        comment_for_payment = request.POST['popup-input-name']
        ApprovalStatus.objects.filter(
            payment=Payments.objects.get(id=request.POST['approval']),
            user=ApprovedFunction.objects.get(
                username=request.user.id)
        ).update(status='OK')
        payments.filter(id=request.POST['approval']).update(
            status_of_payment=f'Согласовано {request.user.last_name} {request.user.first_name}'
        )
        # ========== БЛОК ДЛЯ РАБОТЫ С БОТОМ ПРИ СОГЛАСОВАНИИ ЧЕРЕЗ САЙТ ========= #
        payment_creator = Payments.objects.get(id=request.POST['approval']).creator

        payment_creator_split = payment_creator.split()
        payment_creator_lastname = payment_creator_split[0]
        payment_creator_firstname = payment_creator_split[1]

        payment_creator = ApprovedFunction.objects.get(
            first_name=payment_creator_firstname,
            last_name=payment_creator_lastname).user_name

        user_id = request.user.id
        payment_id = request.POST['approval']
        approval_user = ApprovedFunction.objects.get(
            user_name=request.user.username)
        chat_id = approval_user.chat_id_tg
        keyboard = [[
            telegram.InlineKeyboardButton("Отклонить", 
                callback_data=f'Отклонить {payment_id} {user_id} {payment_creator}')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)

        message_id = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=payment_id),
            message_author=approval_user.user_name
        ).values_list('message_id')[0][0]

        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
        upgrade_message_function(message_id, reply_markup)

        creator_user_rating = ApprovedFunction.objects.get(
            first_name=payment_creator_firstname,
            last_name=payment_creator_lastname).rating_for_approval

        if approval_user.rating_for_approval < 10:
            start_tg_working(payment_id,
                             payment_creator,
                             (approval_user.rating_for_approval+1),
                             comment_for_payment,
                             approval_user.user_name)
        elif approval_user.rating_for_approval == 10:
            start_tg_working(payment_id,
                             payment_creator,
                             approval_user.rating_for_approval,
                             comment_for_payment,
                             approval_user.user_name)      
        # ========== КОНЕЦ БЛОКА ДЛЯ РАБОТЫ С БОТОМ ПРИ СОГЛАСОВАНИИ ЧЕРЕЗ САЙТ ========= #

        return redirect('payment_common_statistic')

    elif request.method == 'POST' and 'reject_payment' in request.POST.keys():
        payment_id = request.POST['reject_payment']
        ApprovalStatus.objects.filter(
            payment=Payments.objects.get(id=payment_id),
            user=ApprovedFunction.objects.get(
                username=request.user.id)
        ).update(
            status='REJECTED',
            rejection_reason=request.POST['popup-input-name']
        )

        payments.filter(id=payment_id).update(
            accountant='',
            date_of_payment=None,
            status_of_payment=f'Отклонено {request.user.last_name} {request.user.first_name}',
            rejection_reason=request.POST['popup-input-name']
        )
        # ========== БЛОК ДЛЯ РАБОТЫ С БОТОМ ПРИ ОТКЛОНЕНИИ ЧЕРЕЗ САЙТ ========= #
        
        # Удаляем все сообщения связанные с заявкой, кроме message_type=create_approve
        messages_for_delete = TelegramMessageActions.objects.filter(
            Q(payment=Payments.objects.get(id=payment_id)) | Q(
                    message_type='comment_button'
                    )).exclude(
                message_type='create_approve'
            ).values_list('chat_id', 'message_id')
        for message_del in messages_for_delete:
            chat_id =  message_del[0]
            message_id = message_del[1]
            try:
                bot.delete_message(chat_id=chat_id, message_id=message_id)
            except:
                    print(f'Сообщения {message_id} не найдено')

        payment_obj = Payments.objects.get(id=payment_id)
        payment_creator = Payments.objects.get(id=payment_id).creator

        payment_creator_split = payment_creator.split()
        payment_creator_lastname = payment_creator_split[0]
        payment_creator_firstname = payment_creator_split[1]

        payment_creator = ApprovedFunction.objects.get(
            first_name=payment_creator_firstname,
            last_name=payment_creator_lastname)

        # Отправляем создателю заявки, что заявка отклонена по какой-то причине
        message = f'Отклонено.\nПричина: {request.POST["popup-input-name"]}'
        message_rej_id = TelegramMessageActions.objects.get(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve',
            message_author=payment_creator.user_name
        ).message_id

        message_obj = bot.send_message(
            chat_id=int(payment_creator.chat_id_tg), text=message, reply_to_message_id=message_rej_id)
        # Записываем сообщение с причиной в базу данных
        save_message_function(payment_obj, payment_creator.chat_id_tg,
            message_obj.message_id, 'rejected_reason_inform', 
            payment_creator.user_name, message, '', False)
        
        messages = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve'
        ).values_list('chat_id', 'message_id', 'message', 'attach')

        for message in messages:
            chat_id_cicle =  message[0]
            message_id_cicle = message[1]
            current_text = message[2]
            attach = message[3]
            words = current_text.split("Статус:")
            new_text = words[0] + f'\nСтатус: ❌ Отклонено\nПричина: {request.POST["popup-input-name"]}'
            if attach == True:
                bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='Markdown')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='Markdown')
        # ========== КОНЕЦ БЛОКА ДЛЯ РАБОТЫ С БОТОМ ПРИ ОТКЛОНЕНИИ ЧЕРЕЗ САЙТ ========= #

        return redirect('payment_common_statistic')
    
    elif request.method == 'POST' and 'pay_payment' in request.POST.keys():
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pay = Payments.objects.get(id=request.POST['pay_payment'])
        payment_id = request.POST['pay_payment']
        pay.status_of_payment = 'Оплачено'
        pay.date_of_payment = now_time
        pay.payer_organization = PayerOrganization.objects.get(
            id=request.POST['payer_organization'])

        if str(pay.project) == 'KINMAC' and str(pay.payer_organization) == 'ИП Лисов Юрий Владимирович ИНН 366315065753' and (
           str(pay.payment_method) == 'Оплата по расчетному счету' or str(pay.payment_method) == 'Оплата по карте на сайте'):
            pay.payment_coefficient = 1.02
        if str(pay.project) == 'KINMAC' and (
           str(pay.payment_method) == 'Перевод на карту' or str(pay.payment_method) == 'Наличная оплата'):
            pay.payment_coefficient = 1.02

        if request.FILES:
            pay.file_of_payment = request.FILES['file_of_payment']
        pay.accountant = f'{request.user.last_name} {request.user.first_name}'
        pay.save()

        payment_obj = Payments.objects.get(id=payment_id)
        payment_creator = Payments.objects.get(id=payment_id).creator

        payment_creator_split = payment_creator.split()
        payment_creator_lastname = payment_creator_split[0]
        payment_creator_firstname = payment_creator_split[1]

        payment_creator = ApprovedFunction.objects.get(
            first_name=payment_creator_firstname,
            last_name=payment_creator_lastname)

        messages = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=request.POST['pay_payment']),
            message_type='create_approve'
        ).values_list('chat_id', 'message_id', 'message', 'attach')

        for message in messages:
            chat_id_cicle =  message[0]
            message_id_cicle = message[1]
            current_text = message[2]
            attach = message[3]
            words = current_text.split("Статус:")
            new_text = words[0] + 'Статус: ✅ Оплачено'
            if attach == True:
                bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='Markdown')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='Markdown')
        
        # Удаляем все сообщения, относящиеся к заявки, кроме тех, у которых message_type='create_approve'
        messages_for_delete = TelegramMessageActions.objects.filter(
            Q(payment=Payments.objects.get(id=payment_id)) | Q(
                    message_type='comment_button'
                    )).exclude(
                message_type='create_approve'
            ).values_list('chat_id', 'message_id')
        for message_del in messages_for_delete:
            chat_id =  message_del[0]
            message_id = message_del[1]
            try:
               bot.delete_message(chat_id=chat_id, message_id=message_id)
            except:
                    print(f'Сообщения {message_id} не найдено')

        # Информирование создателя заявки, что заявка оплачена
        message_id = TelegramMessageActions.objects.get(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve',
            message_author=payment_creator.user_name
        ).message_id
        if Payments.objects.get(id=payment_id).send_payment_file == True:
            file_path = os.path.join(os.getcwd(), 'media/' f'{Payments.objects.get(id=payment_id).file_of_payment}')
            with open(file_path, 'rb') as f:
                message_obj_done = bot.send_document(
                    chat_id=int(payment_creator.chat_id_tg),
                    document=f,
                    caption='Оплачено',
                    reply_to_message_id=message_id)
        else:
            message_obj_done = bot.send_message(
                chat_id=int(payment_creator.chat_id_tg),
                text='Оплачено', reply_to_message_id=message_id)
        save_message_function(pay, payment_creator.chat_id_tg, message_obj_done.message_id,
            'payment_done', payment_creator.user_name, message, '', False)

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


def payment_working_statistic(request):
    """Функция отвечает за отображение краткой таблицы со статистикой"""
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
    
    if request.method == 'POST' and form.is_valid():
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
    if request.method == 'POST' and 'export' in request.POST and form.is_valid():
       
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

        
        return excel_creating_mod(payments)
    
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
    return render(request, 'payment/payment_working_statistic.html', context)

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
                    return self.form_invalid(form, form_class)

    def form_valid(self, form, form_2):
        self.object = form.save()
        form_2.save()
        return redirect('payment_common_statistic')

    def form_invalid(self, form, form_2):
        return self.render_to_response(
            self.get_context_data(form=form, form2=form_2)
        )


def login_by_chat_id(request):
    """
    Функция залогинивает пользователя по его chat_id телеграма
    И направляет на страницу создания заявки
    """
    try:
        chat_id = request.GET.get('chat_id')
        user = ApprovedFunction.objects.get(chat_id_tg=chat_id).user_name
        user_obj = User.objects.get(username=user)
        username = user_obj.username
        password = user_obj.password
        user_auth = authenticate(request, username=username, password=password)
        if user_obj:
            login(request, user_obj)
            return redirect('payment_create')
        else:
            return redirect('login')
    except Exception as e:
        text=f'''Ваш chat_id телеграма не найден в базе данных.
        Система не смогла вас авторизовать автоматически.
        Авторизуйтесь по логину и паролю или обратитесь к администратору'''
        # обработка ошибки и отправка сообщения через бота
        bot.send_message(chat_id=chat_id, text=text)
        return redirect('login')