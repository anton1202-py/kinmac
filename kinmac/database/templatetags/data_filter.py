from django import template

register = template.Library()


@register.filter
def two_elements(string):
    if len(string) > 3:
        return string[:2]

@register.filter
def four_finish_elements(string):
    if len(string) > 4:
        return string[-4:]

@register.filter
def string_filter(string):
    return str(string)