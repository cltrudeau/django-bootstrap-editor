# bseditor.templatetags.bseditortags.py

from django import template
from django.templatetags.static import static

from bseditor.models import Sheet

register = template.Library()

# ============================================================================

@register.simple_tag
def sheetpath(sheet_token):
    try:
        i = int(sheet_token)
        sheet = Sheet.objects.get(id=i)
    except ValueError:
        sheet = Sheet.objects.get(name=sheet_token)

    return static(sheet.filename)
