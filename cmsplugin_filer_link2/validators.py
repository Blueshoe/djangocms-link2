# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_anchor_id(value):
    # HTML5 ID validation is rather lax compared to HTML4: "The value must not contain any space characters."
    # https://www.w3.org/TR/2011/WD-html5-20110525/elements.html#the-id-attribute
    if ' ' in value:
        raise ValidationError(_('Anchor ID must not contain spaces'))
