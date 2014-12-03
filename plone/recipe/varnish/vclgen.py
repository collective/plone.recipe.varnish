# -*- coding: utf-8 -*-
from collections import OrderedDict
from jinja2 import Environment
from jinja2 import PackageLoader
from zc.buildout import UserError
import logging

logger = logging.getLogger(__name__)

jinja2env = Environment(
    loader=PackageLoader('plone.recipe.varnish', 'templates')
)
TEMPLATES_BY_MAJORVERSION = {
    4: jinja2env.get_template('varnish4.vcl.jinja2'),
}

DIRECTOR_TYPES = [
    'round-robin',
    'random',
]


class VclGenerator(object):

    def __init__(self, cfg):

        if cfg.get('major_version', None) not in TEMPLATES_BY_MAJORVERSION:
            self._log_and_raise(
                'Varnish version must be one of {0}. '
                'Use an older version of this recipe to support older '
                'Varnish. Newer versions than listed here are not '
                'supported.'.format(str(TEMPLATES_BY_MAJORVERSION.keys()))
            )
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
                    'director has no name.'.format(
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

    def _vhosting(self):
        vhosting = []
        vhosting_configured = set()

        for idx, backend in enumerate(self.cfg['backends']):
            vh = {}
            vh['setters'] = OrderedDict()

            if self.cfg['balancers']:
                # we support here at the moment only one balancer
                vh['setters']['req.backend_hint'] = \
                    '{0}.backend()'.format(self.cfg['balancers'][0]['name'])
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
                vh['match'].append('req.url ~ "^/{0}"'.format(path))
                vh['setters']['req.http.host'] = '"{0}";'.format(
                    backend['url'].split(':')[0].split('/').pop()
                )
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
                    ' + req.url;'.format(
                        vhm['proto'],
                        backend['url'],
                        vhm['external_port'],
                        vhm['location'],
                    )
                )
            vhosting_configured.add(backend['url'])
        return vhosting

    def __call__(self):
        data = {}
        data['version'] = self.cfg['major_version']
        data['directors'] = self._directors()

        # collect already configure vhostings
        data['purgehosts'] = set()
        data['vhosting'] = self.cfg['vhosting']

        # render vcl file
        template = TEMPLATES_BY_MAJORVERSION[data['version']]
        with open(self.options['config'], 'wt') as fio:
            fio.write(template.render(**data))
        self.options.created(self.options['config'])
