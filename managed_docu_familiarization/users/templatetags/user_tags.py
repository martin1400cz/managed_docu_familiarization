from django import template

register = template.Library()


@register.filter('has_group')
def has_group(user, group_name):
    """Check whether the user is in the specified group.

    Usage:
    {% if request.user|has_group:"TL" %}
    """

    groups = user.cached_groups
    return True if group_name in groups else False


@register.filter
def get_obj_attr(obj, attr):
    return getattr(obj, attr)


@register.filter
def translate_hist_symbol(symbol):
    """Translate the symbol from django simple history, or leave the same.

    + -> added
    ~ -> edited
    ...
    """
    symbol_meaning = {
        '+': '<i class="bi bi-plus-circle"></i> add',
        '~': '<i class="bi bi-pencil"></i> edit',
    }
    return symbol_meaning.get(symbol, symbol)

