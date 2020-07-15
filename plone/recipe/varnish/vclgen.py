# -*- coding: utf-8 -*-
from . import jinja2env
from collections import OrderedDict
from zc.buildout import UserError

import logging


logger = logging.getLogger(__name__)

VCL_TEMPLATE = 'varnish6.vcl.jinja2'

DIRECTOR_TYPES = [
    'round_robin',
    'random',
]


class VclGenerator(object):

    def __init__(self, cfg):
        self.cfg = cfg

    def _log_and_raise(self, message):
        logger.error(message)
        raise UserError(message)

    def _directors(self):
        """load balancing and similar directors
        """
        directors = []

        for director_cfg in self.cfg['directors']:
            if 'name' not in director_cfg:
                self._log_and_raise(
                    'director has no name {0}'.format(
                        director_cfg['type']
                    )
                )

            if director_cfg['type'] not in DIRECTOR_TYPES:
                self._log_and_raise(
                    'director type {0} not supported.'.format(
                        director_cfg['type']
                    )
                )
            director = dict()
            director['type'] = director_cfg['type']
            director['name'] = director_cfg['name']
            director['backends'] = director_cfg['backends']
            directors.append(director)

        return directors

    def _vhostings(self, directors):
        vhosting = []
        vhosting_configured = set()
        for idx, backend in enumerate(self.cfg['backends']):
            vh = {}
            vh['setters'] = OrderedDict()

            use_director = None
            for director in directors:
                if backend['name'] in director['backends']:
                    use_director = director
                    break

            if use_director:
                vh['setters']['req.backend_hint'] = '{0}.backend()'.format(
                    use_director['name']
                )
            else:
                vh['setters']['req.backend_hint'] = backend['name']

            if not backend['url']:
                vhosting.append(vh)
                break
            # we have a backend url if there are more than one backend
            # this was already ensured
            if backend['url'] in vhosting_configured:
                # dup
                continue
            if backend['url'][0] in '/:':
                # match backend based on path only
                path = backend['url'].lstrip(':/')
                vh['match'] = 'req.url ~ "^/{0}"'.format(path)
            elif backend['url'].find(':') != -1:
                # match backend based on hostname and path
                hostname, path = backend['url'].split(':', 1)
                vh['match'] = (
                    'req.http.host ~ "^[{0}](:[0-9]+)?$" && '
                    'req.url ~ "^/{1}"'.format(
                        hostname,
                        path.lstrip(':/')
                    )
                )
            else:
                # set backend based on hostname
                vh['match'] = 'req.http.host ~ "^{0}(:[0-9]+)?$"'.format(
                    backend['url']
                )

            # translate into vhm url if defined for hostname
            if backend['url'] in self.cfg['zope2_vhm_map']:
                # this could be more generic, needs refactoring
                vhm = self.cfg['zope2_vhm_map'][backend['url']]
                vh['setters']['req.url'] = (
                    '"/VirtualHostBase/{0}/{1}:{2}/{3}/VirtualHostRoot"'
                    ' + req.url'.format(
                        vhm['proto'],
                        backend['url'],
                        vhm['external_port'],
                        vhm['location'].lstrip('/'),
                    )
                )
            vhosting_configured.add(backend['url'])
            vhosting.append(vh)
        return vhosting

    def _purgehosts(self):
        purgehosts = set(self.cfg['purgehosts'])
        purgehosts.update(
            [_['host'] for _ in self.cfg['backends'] if 'host' in _])
        return purgehosts

    def __call__(self):
        data = {}
        data['backends'] = self.cfg['backends']
        data['directors'] = self._directors()
        data['vhosting'] = self._vhostings(data['directors'])
        data['purgehosts'] = self._purgehosts()
        data['custom'] = self.cfg['custom']
        data['cookiewhitelist'] = self.cfg['cookiewhitelist']
        data['cookiepass'] = self.cfg['cookiepass']
        data['code404page'] = self.cfg['code404page']
        data['gracehealthy'] = self.cfg['gracehealthy']
        data['gracesick'] = self.cfg['gracesick']
        data['healthprobeurl'] = self.cfg.get('healthprobeurl') or '/ok'
        data['healthprobetimeout'] = self.cfg.get('healthprobetimeout') or '5s'
        data['healthprobeinterval'] = self.cfg.get('healthprobeinterval') or '15s'
        data['healthprobewindow'] = self.cfg.get('healthprobewindow') or '10'
        data['healthprobethreshold'] = self.cfg.get('healthprobethreshold') or '8'
        data['healthprobeinitial'] = self.cfg.get('healthprobeinitial') or None

        data['vcl_version'] = 4.0
        # render vcl file
        template = jinja2env.get_template(VCL_TEMPLATE)
        return template.render(**data)
