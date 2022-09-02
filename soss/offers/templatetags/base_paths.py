from django import template
from django.conf import settings
register = template.Library()

def js_prefix():
    return settings.JS_PREFIX


def css_prefix():
    return settings.CSS_PREFIX

register.simple_tag(js_prefix)
register.simple_tag(css_prefix)