# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.translation import activate
from django.utils.translation import gettext as _

from cmsplugin_filer_link2.management.commands import check_links
from .models import LinkHealthState


class LinkStateAdmin(admin.ModelAdmin):
    list_display = ('link_name', 'link_to', 'state', 'on_page', 'detected')
    list_filter = ('state',)

    change_list_template = 'admin/cmsplugin_filer_link/change_list.html'

    def changelist_view(self, request, extra_context=None):
        context = {
            'not_found_errors': LinkHealthState.objects.filter(state=LinkHealthState.NOT_REACHABLE),
            'server_errors': LinkHealthState.objects.filter(state=LinkHealthState.SERVER_ERROR),
            'redirected_links': LinkHealthState.objects.filter(state=LinkHealthState.REDIRECT),
            'bad_configured_links': LinkHealthState.objects.filter(state=LinkHealthState.BAD_CONFIGURED),
            'error_count': LinkHealthState.objects.all().count()
        }
        context.update(extra_context or {})
        return super(LinkStateAdmin, self).changelist_view(request, context)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(LinkStateAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_urls(self):
        urlpatterns = super(LinkStateAdmin, self).get_urls()

        link_health_state_custom_urls = [
            url(r'^update-health-states/$', self.admin_site.admin_view(self.update_health_states),
                name='%s_%s_update_health_state' % (self.model._meta.app_label, self.model._meta.model_name))
        ]

        return link_health_state_custom_urls + urlpatterns

    def update_health_states(self, request):
        cmd = check_links.Command()
        cmd.handle()
        return redirect('admin:%s_%s_changelist' % (self.model._meta.app_label, self.model._meta.model_name))

    def link_name(self, obj):
        return obj.link
    link_name.allow_tags = True
    link_name.short_description = _('Link name')

    def on_page(self, obj):
        activate(obj.link.language)
        try:
            return mark_safe('<a href="{link}" >{link}</a>'.format(link=obj.link.page.get_absolute_url()))
        except AttributeError:
            # this can happen when a link is not embedded on a page, but e.g. in an app (e.g. AldrynNewsblog)
            return _('Not embedded on a page, but for example in an app.')
    on_page.allow_tags = True
    on_page.short_description = _('On page')

    def link_to(self, obj):
        if obj.state != LinkHealthState.BAD_CONFIGURED:
            activate(obj.link.language)
            return mark_safe('<a href="{link}" >{link}</a>'.format(link=obj.link.get_link()))
    link_to.allow_tags = True
    link_to.short_description = _('Links to')


admin.site.register(LinkHealthState, LinkStateAdmin)
