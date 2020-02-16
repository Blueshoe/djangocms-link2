# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.urls import NoReverseMatch
from django.db import models
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from cms.models import CMSPlugin

from filer.fields.file import FilerFileField

from djangocms_attributes_field.fields import AttributesField

from cmsplugin_filer_link2.fields import Select2PageField
from cmsplugin_filer_link2.validators import validate_anchor_id

DEFULT_LINK_STYLES = (
    (" ", "Default"),
)

LINK_STYLES = getattr(settings, "FILER_LINK_STYLES", DEFULT_LINK_STYLES)

EXCLUDED_KEYS = ['class', 'href', 'target', ]


class FilerLink2Plugin(CMSPlugin):
    name = models.CharField(_('name'), max_length=255)
    url = models.CharField(_('url'), blank=True, null=True, max_length=2000,
                           help_text=_('The url must specify the protocol, e.g. https://DOMAIN.tld'))
    page_link = Select2PageField(
        verbose_name=_('page'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    persistent_page_link = models.CharField(_('internal url'), blank=True, null=True, max_length=2000)
    mailto = models.EmailField(_('mailto'), blank=True, null=True, max_length=254)
    link_style = models.CharField(_('link style'), max_length=255,
                                  choices=LINK_STYLES, default=LINK_STYLES[0][0])
    new_window = models.BooleanField(_('new window?'), default=False,
                                     help_text=_('Do you want this link to open a new window?'))
    file = FilerFileField(blank=True, null=True, on_delete=models.SET_NULL)
    link_attributes = AttributesField(excluded_keys=EXCLUDED_KEYS, blank=True,
                                      help_text=_('Optional. Adds HTML attributes to the rendered link.'))

    encrypt_mailto = models.BooleanField(_('Encryption of Mailto'), default=False,
                                         help_text=_('Encrypt the mailto, as protection against bots collecting mails '
                                                     'addresses.'))

    anchor_id = models.CharField(
        _('Anchor ID'),
        blank=True,
        max_length=100,
        validators=[validate_anchor_id]
    )

    cmsplugin_ptr = models.OneToOneField(
        to=CMSPlugin,
        related_name='%(app_label)s_%(class)s',
        parent_link=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    def clean(self):
        super(FilerLink2Plugin, self).clean()
        configured_destinations = [d for d in
                                   ('url', 'page_link', 'mailto', 'file')
                                   if getattr(self, d) is not None and getattr(self, d) != '']
        if len(configured_destinations) == 0:
            raise ValidationError(_('Please choose a destination'))
        elif len(configured_destinations) > 1:
            raise ValidationError(
                _('Please only choose one destination! You set: {}'.format(', '.join(configured_destinations))))

    def save(self, *args, **kwargs):
        super(FilerLink2Plugin, self).save(*args, **kwargs)
        # delete link health state
        LinkHealthState.objects.filter(link=self).delete()

    def get_encrypted_mailto(self):
        name, domain = self.mailto.split('@')
        return 'javascript:window.location.href = \'mailto:\' + [\'{}\', \'{}\'].join(\'@\')'.format(name, domain)

    def get_name(self):
        if self.encrypt_mailto and self.mailto:
            if self.name == self.mailto:
                name, domain = self.name.split('@')
                # escape name and domain for security reasons
                return mark_safe('{}<!---->@<!---->{}'.format(escape(name), escape(domain)))
        else:
            return self.name

    def get_link(self):
        if self.file:
            link = self.file.url
        elif self.mailto:
            if self.encrypt_mailto:
                link = _(self.get_encrypted_mailto())
            else:
                link = 'mailto:{}'.format(_(self.mailto))
        elif self.url:
            link = _(self.url)
        elif self.page_link:
            try:
                link = self.page_link.get_absolute_url()
            except NoReverseMatch:
                # if this internal link doesn't work anymore, we mark it not reachable
                self.set_linkstate(LinkHealthState.NOT_REACHABLE)
                # return old internal link and send user to 404
                link = self.persistent_page_link
            else:
                # check if the target page has been moved or renamed and update accordingly
                if link != self.persistent_page_link:
                    self.persistent_page_link = link
                    self.save()
        elif self.persistent_page_link:
            # happens when this link instance pointed to a removed page
            self.set_linkstate(LinkHealthState.NOT_REACHABLE)
            link = self.persistent_page_link
        else:
            link = ''
        # Append anchor ID to url
        if self.anchor_id:
            link += '#{}'.format(self.anchor_id)
        return link or ''

    def set_linkstate(self, state):
        if state is None:
            LinkHealthState.objects.filter(link=self).delete()
        else:
            LinkHealthState.objects.update_or_create(link=self, defaults={'state': state})

    def get_linkstate(self):
        try:
            return self.linkhealth.state
        except ObjectDoesNotExist:
            return None

    @property
    def active_destination(self):
        """ The active destination determines which destination tab should be set to active. If the field is not set
        yet, we return None
        :return: field_name: str
        """
        configured_destinations = [d for d in
                                   ('url', 'page_link', 'mailto', 'file')
                                   if getattr(self, d) is not None and getattr(self, d) != '']
        if len(configured_destinations) == 0:
            return None
        return configured_destinations[0]


class LinkHealthState(models.Model):
    NOT_REACHABLE = '4xx'
    REDIRECT = '3xx'
    SERVER_ERROR = '5xx'
    BAD_CONFIGURED = 'bad'
    TIMEOUT = 'to'

    LINK_STATES = (
        (REDIRECT, _('Redirected')),
        (NOT_REACHABLE, _('Not reachable')),
        (SERVER_ERROR, _('Server error')),
        (BAD_CONFIGURED, _('Bad configured')),
        (TIMEOUT, _('Timeout')),
    )

    link = models.OneToOneField(FilerLink2Plugin, unique=True, related_name='linkhealth',
                                verbose_name=_('Link name'), on_delete=models.CASCADE)
    state = models.CharField(max_length=3, choices=LINK_STATES, verbose_name=_('State'))
    detected = models.DateTimeField(auto_now=True, verbose_name=_('Detected on'),
                                    help_text=_('Date and time when the faulty link state was detected.'))

    def __str__(self):
        return _(u'Link state for: {}').format(self.link.name)

    class Meta:
        verbose_name = _('Link Health State')
        verbose_name_plural = _('Link Health States')
