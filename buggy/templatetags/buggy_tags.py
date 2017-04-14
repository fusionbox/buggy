from django import template
from django.utils.html import format_html
from django.utils.formats import date_format
from django.utils import timezone
from django.conf import settings

from babel.dates import format_timedelta

register = template.Library()


@register.filter
def relativedate(d):
    return format_html(
        '<time title="{}" datetime="{}">{} ago</time>',
        date_format(timezone.localtime(d), settings.DATETIME_FORMAT),
        d.isoformat(),
        format_timedelta(timezone.now() - d),
    )


@register.filter
def absolutedate(d):
    return format_html(
        '<time title="{} ago" datetime="{}">{}</time>',
        format_timedelta(timezone.now() - d),
        d.isoformat(),
        date_format(timezone.localtime(d), settings.DATETIME_FORMAT),
    )
