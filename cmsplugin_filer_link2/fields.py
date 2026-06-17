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
        # NB: do NOT load jQuery from an external CDN here. The Django admin ships
        # its own jQuery and runs jQuery.noConflict(true) in admin/js/jquery.init.js,
        # which removes the global the old inline init relied on; when the CDN was
        # unreachable the page-select silently fell back to a raw, unstyled tree.
        # The init script below is self-contained and binds select2 to django.jQuery.
        # select2 itself is intentionally NOT listed here: loading it via Media runs
        # it against the post-noConflict (undefined) global and logs a "jQuery not
        # found" error on every page; _build_script loads it on demand instead.
        js = ['django_select2/django_select2.js']
        # select2's own JS is loaded on demand (see _build_script) to dodge the
        # noConflict jQuery-timing issue, but its stylesheet has no such problem
        # and is safe to ship via Media. Without it the results render as an
        # unstyled, inline tree that overlaps the rest of the plugin form.
        css = {
            'screen': tuple(settings.SELECT2_CSS),
        }

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
        # Self-contained init that does not depend on a global `$`/`jQuery` (which
        # the admin's noConflict(true) removes) nor on an external CDN. It binds to
        # django.jQuery and, if select2 has not attached to it, loads select2 from
        # the project's own static files before initialising.
        from django.contrib.staticfiles.storage import staticfiles_storage
        select2_url = staticfiles_storage.url(settings.SELECT2_JS[0]) if settings.SELECT2_JS else ''
        result += """
        <script>
        (function () {
            function ready(cb) {
                if (document.readyState !== 'loading') { cb(); }
                else { document.addEventListener('DOMContentLoaded', cb); }
            }
            function getJQ() {
                if (typeof window.django !== 'undefined' && django.jQuery) { return django.jQuery; }
                return window.jQuery || window.$ || null;
            }
            function start($) {
                var inst = $('[name="%(name)s_1"]').select2({ dropdownAutoWidth: true });
                setTimeout(function () { inst.trigger('change'); }, 300);
            }
            function init() {
                var $ = getJQ();
                if (!$) { return setTimeout(init, 50); }
                if ($.fn && typeof $.fn.select2 === 'function') { return start($); }
                // select2 is not bound to this jQuery yet: make it global and load it.
                window.jQuery = $;
                var s = document.createElement('script');
                s.src = '%(select2_url)s';
                s.onload = function () { start($); };
                document.head.appendChild(s);
            }
            ready(init);
        })();
        </script>
        """ % {
            'name': name,
            'select2_url': select2_url,
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
