# todo/templatetags/todo_extras.py

from django import template

register = template.Library()

@register.filter
def format_timedelta(value):
    """Format a timedelta object into HH:MM:SS string."""
    if not value:
        return ""
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@register.filter
def progress_bar(done, total):
    try:
        pourcentage = (done / total) * 100
        return "{:.0f}".format(pourcentage)
    except ZeroDivisionError:
        return "0"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])


@register.filter
def format_duree(td):
    total_seconds = int(td.total_seconds())
    heures, reste = divmod(total_seconds, 3600)
    minutes, _ = divmod(reste, 60)
    return f"{heures}h{minutes:02d}min"
