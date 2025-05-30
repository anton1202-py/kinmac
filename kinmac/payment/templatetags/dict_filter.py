from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def multiplicity(value, arg):
    return value * arg


@register.filter
def divide(value, arg):
    if arg == 0:
        return 0
    return value / arg

@register.filter
def float_make(value):
    return float(value)

@register.filter
def round_number_two(value):
    if value:
        return round(value, 2)
    else:
        return value