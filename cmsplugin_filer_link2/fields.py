# -*- coding: utf-8 -*-
from django.conf import settings
from cms.forms.fields import PageSelectFormField
from cms.forms.utils import get_site_choices, get_page_choices
from cms.forms.widgets import PageSelectWidget
from cms.models.fields import PageField
from django.forms import Select
# This import is needed to make sure the django-select2 settings are actually loaded. Since django-select2 uses
# the django-appconf package to load some settings we cannot be certain the these settings are loaded when this
# module is imported.
from django_select2.forms import Select2Widget  # noqa


class PageSelect2Widget(PageSelectWidget):

    class Media:
        js = ('https://code.jquery.com/jquery-2.1.4.min.js', settings.SELECT2_JS, 'django_select2/django_select2.js')
        # css = {
        #     'screen': (settings.SELECT2_CSS, )
        # }

    def _build_widgets(self):
        site_choices = get_site_choices()
        page_choices = get_page_choices()
        self.site_choices = site_choices
        self.choices = page_choices
        self.widgets = (Select(choices=site_choices),
                        Select(choices=[('', '----')]),
                        Select(choices=self.choices, attrs={'style': "display:none;"}),
                        )

    def _build_script(self, name, value, attrs={}):
        """Bit of a dirty workaround since there is no event we can catch to update the select2 instance. """
        result = super(PageSelect2Widget, self)._build_script(name, value, attrs={})
        result += """
        <script>
            var select2Instance = $('[name="%(name)s_1"]').select2({ dropdownAutoWidth : true });
            setTimeout(function () {select2Instance.trigger('change')}, 300);
        </script>
        """ % {
            'name': name
        }
        return result

    def get_context(self, name, value, attrs):
        ctx = super(PageSelect2Widget, self).get_context(name, value, attrs)
        # del ctx['widget']['script_init']
        return ctx


class PageSelect2FormField(PageSelectFormField):
    widget = PageSelect2Widget


class Select2PageField(PageField):
    default_form_class = PageSelect2FormField
