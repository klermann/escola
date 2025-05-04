from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    # Garante que a chave seja tratada como string
    key = str(key)
    return dictionary.get(key, '')