import re

from django.core.exceptions import ValidationError
from django.db import models


def validate_credit_card(value):
    if not value.isdigit():
        raise ValidationError('Номер карты должен состоять только из цифр')
    if len(value) != 16:
        raise ValidationError('Номер карты должен содержать 16 цифр')


def ValidateCharacters(number):
    """ Checks to make sure string only contains valid characters """
    return re.compile('^[0-9 ]*$').match(number) != None


def StripToNumbers(number):
    """ remove spaces from the number """
    if ValidateCharacters(number):
        result = ''
        rx = re.compile('^[0-9]$')
        for d in number:
            if rx.match(d):
                result += d
        return result
    else:
        raise Exception('Number has invalid digits')


def format_phone_number(phone_number):
    clean_number = ''.join(filter(str.isdigit, str(phone_number)))
    formatted_number = '+7({}) {} {} {}'.format(
        clean_number[1:4], clean_number[4:7], clean_number[7:9], clean_number[9:11])
    return formatted_number
