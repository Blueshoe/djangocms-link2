import requests

from django.core.management.base import BaseCommand
from django.urls import NoReverseMatch

from django.utils.translation import activate
from requests.exceptions import ConnectionError, MissingSchema, InvalidSchema, ReadTimeout

from django.conf import settings

from cmsplugin_filer_link2.models import FilerLink2Plugin, LinkHealthState


class Command(BaseCommand):
    help = 'Check all links for the availability of their destination'

    def add_arguments(self, parser):
        parser.add_argument('--timeout', default=60, type=int, nargs='?')
        parser.add_argument('--no-agent', default=False, type=bool, nargs='?')

    def check_with_request(self, url, timeout, use_agent=True):
        LINK_DOMAIN = getattr(settings, 'LINK_DOMAIN', None)
        if url.startswith('/'):
            if not LINK_DOMAIN:
                raise Exception('No domain for found - cannot check relative paths. Please configure LINK_DOMAIN.')
            url = '{}{}'.format(LINK_DOMAIN, url)

        if url and url.startswith('#'):
            return

        headers = {}

        if use_agent:
            headers['User-Agent'] = 'Link Checker - Brought to you by Blueshoe'

        try:
            r = requests.get(url, verify=False, timeout=timeout, headers=headers)
        except ReadTimeout:
            return LinkHealthState.TIMEOUT
        except ConnectionError:
            return LinkHealthState.SERVER_ERROR
        except MissingSchema:
            return LinkHealthState.BAD_CONFIGURED
        except InvalidSchema:
            return LinkHealthState.BAD_CONFIGURED
        return {
            # we are only interested in bad status codes
            '3': LinkHealthState.REDIRECT,
            '4': LinkHealthState.NOT_REACHABLE,
            '5': LinkHealthState.SERVER_ERROR
        }.get(str(r.status_code)[0])

    def handle(self, *args, **options):
        timeout = options['timeout']
        no_agent = options['no_agent']

        all_links = FilerLink2Plugin.objects.all()
        self.stdout.write('Checking {num} link-instances'.format(num=all_links.count()))

        for link in all_links:
            status = None
            if link.file:
                status = self.check_with_request(link.file.url, timeout=timeout, use_agent=not no_agent)
            elif link.url:
                status = self.check_with_request(link.url, timeout=timeout, use_agent=not no_agent)
            elif link.page_link:
                try:
                    # see if we can resolve the page this link points to
                    activate(link.language)
                    link.page_link.get_absolute_url()
                except NoReverseMatch:
                    status = LinkHealthState.NOT_REACHABLE
            link.set_linkstate(status)
