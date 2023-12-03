from payment.models import TelegramMessageActions


def save_message_function(payment_object, chat_id, message_id,
                          message_type, message_author, message, attach):
    """Функция отвечает за сохранение сообщения в чате с KINMAC ботом в базу данных.
    Входящие переменные:
    payment_object - объект класса Payments. Таблица TelegramMessageActions связана
        с таблицей Payments через ключ ForeignKey.
        payment_object надится путем Payments.objects.get(id=payment_id).
    chat_id - идентификатор пользователя телеграм, который отрпавляет сообщение или
        которому бот отрпавляет сообщение.
    message_id - идентификатор сообщений в чате с ботом. У каждого сообщения 
        свой персональный номер.
    message_type - тип сообщений, которые отрпавляет бот или пользователь.
        Есть несколько типов:
        create_approve - сообщения с уведомлением, что заявка создана и еще нужно
        согласовать или оплатить.
        reject_reason - сообщение о причине отклонения заявки.
        payment_organizations - сообщение с выбором плательщика для заявки.
        payment_file - сообщение с файлом платежки после оплаты заявки.
        payment_done - сообщения связанные с уведомлением об оплате заявки.
        reject_reason_answer - уведомления создателю заявки о причины ее отклонения.
        answer - ответы пользователя на сообщения бота, если они укладываются в сценарий.
    message_author - автор сообщения или кому отправил сообщеине бот.
    message - сохраняемое сообщение.
    attach - Тип Boolean. Указывает есть в сообщении вложение или нет.
        или нет.
    """
    telegram_message_attach = TelegramMessageActions(
        payment=payment_object,
        chat_id=chat_id,
        message_id=message_id,
        message_type=message_type,
        message_author=message_author,
        message=message,
        attach=attach
    )
    telegram_message_attach.save()