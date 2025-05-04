from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Divide uma string pelo delimitador"""
    return value.split(delimiter)

@register.filter
def get_item(dictionary, key):
    """Obtém um item de dicionário"""
    return dictionary.get(key, {})