# -*- coding: utf-8 -*-
import logging
import os
import zc.buildout
from .vclgen import VclGenerator

DOWNLOAD_URLS = {
    '4': 'https://repo.varnish-cache.org/source/varnish-4.0.0.tar.gz',
}

CONFIG_EXCLUDES = set(
    [
        'zope2_vhm_map',
        'zope2_vhm_port',
        'zope2_vhm_ssl',
        'zope2_vhm_ssl_port',
        'backends',
        'verbose-headers',
        'saint-mode',
    ]
)


class ConfigureRecipe(object):

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout
        self.logger = logging.getLogger(self.name)
        self.options.setdefault(
            'location',
            os.path.join(buildout['buildout']['parts-directory'], self.name)
        )

        # Expose the download url of a known-good Varnish release
        # Set some default options
        self.options.setdefault('varnish_version', '4')
        if self.options['varnish_version'] in DOWNLOAD_URLS:
            url = DOWNLOAD_URLS[self.options['varnish_version']]
        else:
            self._log_and_raise(
                'Varnish {0} is not supported.'.format(
                    self.options['varnish_version']
                )
            )
        self.options.setdefault('download-url', url)
        self.options.setdefault('bind', '127.0.0.1:8000')
        self.daemon = self.options['daemon']
        self.options.setdefault('cache-type', 'file')
        self.options.setdefault(
            'cache-location',
            os.path.join(self.options['location'], 'storage')
        )
        self.options.setdefault('cache-size', '256M')
        self.options.setdefault('runtime-parameters', '')
        if 'config' in self.options:
            if set(self.options.keys()).intersection(CONFIG_EXCLUDES):
                msg = ('When config= option is specified the following '
                       'options cant be used: ')
                msg += ' '.join(CONFIG_EXCLUDES)
                self.logger.error(msg)
                raise zc.buildout.UserError(msg)
            self.options['generate_config'] = 'false'
        else:
            self.options['generate_config'] = 'true'
            self.options.setdefault('verbose-headers', 'off')
            self.options.setdefault('saint-mode', 'off')
            self.options.setdefault('balancer', 'none')
            self.options.setdefault('backends', '127.0.0.1:8080')
            self.options['config'] = os.path.join(self.options['location'],
                                                  'varnish.vcl')

        self.options.setdefault('connect-timeout', '0.4s')
        self.options.setdefault('first-byte-timeout', '300s')
        self.options.setdefault('between-bytes-timeout', '60s')
        self.options.setdefault('purge-hosts', '')
        self.options.setdefault('cookie-fixup', 'on')

        # Test for valid bind value
        self.options['bind'] = self.options.get('bind').lstrip(':')
        bind = self.options['bind'].split(':')
        if len(bind) == 1 and bind[0].isdigit():
            self.options['bind-host'] = ''
            self.options['bind-port'] = bind[0]
            self.options['bind'] = ':' + bind[0]
        elif len(bind) == 2 and bind[1].isdigit():
            self.options['bind-host'] = bind[0]
            self.options['bind-port'] = bind[1]
        else:
            self.logger.error('Invalid syntax for bind')
            raise zc.buildout.UserError('Invalid syntax for bind')

    def _log_and_raise(self, message):
        self.logger.error(message)
        raise zc.buildout.UserError(message)

    def install(self):
        location = self.options['location']

        if not os.path.exists(location):
            os.mkdir(location)
        self.options.created(location)

        self.addVarnishRunner()
        if self.options['generate_config'] == 'true':
            self.createVarnishConfig()

        return self.options.created()

    def update(self):
        pass

    def addVarnishRunner(self):
        target = os.path.join(
            self.buildout['buildout']['bin-directory'],
            self.name
        )
        parameters = self.options['runtime-parameters'].strip().split()

        with open(target, 'wt') as tf:
            print >>tf, '#!/bin/sh'
            print >>tf, 'exec %s \\' % self.daemon
            if 'user' in self.options:
                print >>tf, '    -p user=%s \\' % self.options['user']
            if 'group' in self.options:
                print >>tf, '    -p group=%s \\' % self.options['group']
            print >>tf, '    -f "%s" \\' % self.options['config']
            print >>tf, '    -P "%s" \\' % \
                os.path.join(self.options['location'], 'varnish.pid')
            print >>tf, '    -a %s \\' % self.options['bind']
            if self.options.get('telnet', None):
                print >>tf, '    -T %s \\' % self.options['telnet']
            if self.options['cache-type'] == 'malloc':
                print >>tf, '    -s %s,%s \\' % (
                    self.options['cache-type'],
                    self.options['cache-size']
                )
            else:
                print >>tf, '    -s %s,"%s",%s \\' % (
                    self.options['cache-type'],
                    self.options['cache-location'],
                    self.options['cache-size']
                )
            if self.options.get('mode', 'daemon') == 'foreground':
                print >>tf, '    -F \\'
            if self.options.get('name', None):
                print >>tf, '    -n %s \\' % self.options['name']
            for parameter in parameters:
                print >>tf, '    -p %s \\' % (parameter)
            print >>tf, '    "$@"'
        os.chmod(target, 0755)
        self.options.created(target)

    def _process_backends(self):
        result = {}
        raw_backends = [
            _.rsplit(':', 2)
            for _ in self.options['backends'].strip().split()
        ]
        # consistency checks
        if len(raw_backends) > 1:
            lengths = set([len(x) for x in raw_backends])
            if lengths != set([3]):
                self._log_and_raise(
                    'When using multiple backends a hostname '
                    'must be given for each client'
                )
        for idx, raw_backend in enumerate(raw_backends):
            backend = {
                'name': 'backend_{0:03d}'.format(idx)

            }
            try:
                if len(backend) == 3:
                    url, host, port = raw_backend
                else:
                    host, port = raw_backend
                    url = None
            except ValueError:
                self._log_and_raise(
                    'Invalid syntax for backend: {0}'.format(
                        ':'.join(raw_backend)
                    )
                )
                raise zc.buildout.UserError('Invalid syntax for backends')
            backend['url'] = url
            backend['host'] = host
            backend['port'] = port
            backend['connect_timeout'] = self.options['connect-timeout']
            backend['first_byte_timeout'] = self.options['first-byte-timeout']
            backend['between_bytes_timeout'] = \
                self.options['between-bytes-timeout']

            result.append(backend)

        return result

    def _process_zope_vhm_map(self, backends):
        result = {}

        vhm_external_port = self.options.get(
            'zope2_vhm_port',
            self.options['bind-port']
        )
        vhm_proto = 'http'
        if self.options.get('zope2_vhm_ssl', False) == 'on':
            vhm_external_port = self.options.get('zope2_vhm_ssl_port', '443')
            vhm_proto = 'https'

        for line in self.options.get('zope2_vhm_map', '').split():
            domain, location = line.split(':')
            result[domain.strip()] = {
                'location': location.strip(),
                'proto': vhm_proto,
                'external_port': vhm_external_port,
            }

        # consistency checks
        if result:
            lengths = set([len(x) for x in backends])
            if lengths != set([3]):
                self._log_and_raise(
                    'When using VHM a hostname must be given for each backend'
                )
        return result

    def _process_balancers(self, balancer, backends):
        """if theres is a balancer configured, all backends are assigned.

        this could be refactored in future to support multiple balancers.
        """
        result = []
        if balancer != 'none':
            record = {
                'type': balancer,
                'name': 'balancer_0',
                'backends': [_['name'] for _ in backends],
            }
            result.append(record)
        return result

    def createVarnishConfig(self):
        major_version = self.options['varnish_version']
        config = {}
        config['version'] = major_version

        # enable verbose varnish headers
        config['verbose'] = self.options['verbose-headers'] == 'on'
        config['saint'] = self.options['saint-mode'] == 'on'
        if config['saint'] and config['verbose']:
            self._log_and_raise(
                'When using saint-mode verbose headers must be off'
            )

        # fixup cookies for better plone caching
        config['cookiefixup'] = self.options['cookie-fixup'] == 'on'

        # inject custom vcl
        config['custom'] = {}
        for name in ('vcl_recv', 'vcl_hit', 'vcl_miss', 'vcl_fetch',
                     'vcl_deliver', 'vcl_pipe'):
            config['custom'][name] = self.options.get(name, '')

        config['backends'] = self._process_backends()
        config['balancers'] = self._process_balancers(
            self.options['balancer'].strip(),
            config['backends']
        )
        config['zope2_vhm_maps'] = self._process_zope_vhm_map(
            config['backends']
        )
        config['purgehosts'] = set([])

        # collect already configure vhostings
        config['vhosting'] = list()


        # # if we have backends with 3-tuple style configuration, then
        # # we need a 404 page at the end
        # if len(config['backends'][0]) == 3:
        #     config['code404page'] = True

        # build the purge host string
        for segment in self.options['purge-hosts'].split():
            segment = segment.strip()
            if segment:
                config['purgehosts'].add(segment)

        vclgenerator = VclGenerator(config)
        filedata = vclgenerator()
        with open(self.options['config'], 'wt') as fio:
            fio.write(filedata)
        self.options.created(self.options['config'])
