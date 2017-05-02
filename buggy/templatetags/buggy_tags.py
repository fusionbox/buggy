from django import template
from django.utils.html import format_html
from django.utils.formats import date_format
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib import staticfiles

from babel.dates import format_timedelta

register = template.Library()


@register.filter
def relativedate(d):
    return format_html(
        '<time class="relativeDate" title="{}" datetime="{}">{} ago</time>',
        date_format(timezone.localtime(d), settings.DATETIME_FORMAT),
        d.isoformat(),
        format_timedelta(timezone.now() - d),
    )


@register.filter
def absolutedate(d):
    return format_html(
        '<time class="absoluteDate" title="{} ago" datetime="{}">{}</time>',
        format_timedelta(timezone.now() - d),
        d.isoformat(),
        date_format(timezone.localtime(d), settings.DATETIME_FORMAT),
    )


@register.simple_tag
def svg(svg_file):
    filename = staticfiles.finders.find(svg_file)
    if not filename:
        raise IOError('Static file %r not found.' % svg_file)
    with open(filename) as f:
        return mark_safe(f.read())
