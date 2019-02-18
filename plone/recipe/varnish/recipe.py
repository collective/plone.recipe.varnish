# -*- coding: utf-8 -*-
from . import jinja2env
from plone.recipe.varnish.vclgen import VclGenerator
from zc.recipe.cmmi import Recipe as CMMIRecipe
from zc.recipe.cmmi import system

import logging
import os
import re
import zc.buildout


DEFAULT_DOWNLOAD_URLS = {
    '4.0': 'http://varnish-cache.org/_downloads/varnish-4.0.5.tgz',
    '4.1': 'http://varnish-cache.org/_downloads/varnish-4.1.11.tgz',
    '4': 'http://varnish-cache.org/_downloads/varnish-4.1.11.tgz',
    '5.0': 'http://varnish-cache.org/_downloads/varnish-5.0.0.tgz',
    '5.1': 'http://varnish-cache.org/_downloads/varnish-5.1.3.tgz',
    '5.2': 'http://varnish-cache.org/_downloads/varnish-5.2.1.tgz',
    '5': 'http://varnish-cache.org/_downloads/varnish-5.2.1.tgz',
    '6': 'http://varnish-cache.org/_downloads/varnish-6.0.0.tgz',
}
DEFAULT_VERSION = '5'
DEFAULT_VCL_VERSION = '4.0'

COOKIE_WHITELIST_DEFAULT = """\
statusmessages
__ac
_ZopeId
__cp
"""

COOKIE_PASS_DEFAULT = """\
"__ac(|_(name|password|persistent))=":"\.(js|css|kss)$"
"""
COOKIE_PASS_RE = re.compile('"(.*)":"(.*)"')


class BaseRecipe(object):

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout
        self.logger = logging.getLogger(self.name)

    def _version_check(self):
        """check if version is supported
        """
        if self.options['varnish_version'] not in DEFAULT_DOWNLOAD_URLS:
            self._log_and_raise(
                'Varnish {0} is not supported.'.format(
                    self.options['varnish_version']
                )
            )

    def _log_and_raise(self, message):
        """log error first and then raise buildout Exception
        """
        self.logger.error(message)
        raise zc.buildout.UserError(message)

    def _process_bind(self):
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
            self._log_and_raise('Invalid syntax for bind')

    def get_from_section(self, part, key, default):
        if part not in self.buildout:
            return default
        if key not in self.buildout[part]:
            return default
        return self.buildout[part][key]

    def install(self):
        pass

    def update(self):
        pass


class BuildRecipe(CMMIRecipe, BaseRecipe):

    def __init__(self, buildout, name, options):
        BaseRecipe.__init__(self, buildout, name, options)
        self.options.setdefault('varnish_version', DEFAULT_VERSION)
        self._version_check()
        self.options.setdefault(
            'url',
            DEFAULT_DOWNLOAD_URLS[options.get('varnish_version')]
        )
        self.options.setdefault('jobs', '4')
        CMMIRecipe.__init__(self, buildout, name, self.options)

    def cmmi(self, dest):
        """Do the 'configure; make; make install' command sequence.

        When this is called, the current working directory is the
        source directory.  The 'dest' parameter specifies the
        installation prefix.

        This is overidden in order to enable parallel jobs in make.
        """
        options = self.configure_options
        if options is None:
            options = '--prefix="%s"' % dest
        if self.extra_options:
            options += ' %s' % self.extra_options

        # C
        system('%s %s' % (self.configure_cmd, options))

        # M
        base_make = 'make'
        if int(self.options.get('jobs')) > 1:
            base_make += ' -j {0}'.format(self.options.get('jobs'))
        system(base_make)

        # MI
        system('make install')

        # TODO: future task: integrate vmods

        # set daemon location
        self.options['daemon'] = os.path.join(
            self.options['location'],
            'sbin',
            'varnishd'
        )


class ConfigureRecipe(BaseRecipe):

    def __init__(self, buildout, name, options):
        super(ConfigureRecipe, self).__init__(buildout, name, options)

        self.options.setdefault('build-part', 'varnish-build')
        self.options.setdefault(
            'varnish_version',
            self.get_from_section(
                self.options['build-part'],
                'varnish_version',
                DEFAULT_VERSION
            )
        )
        self._version_check()
        self.options.setdefault('vcl-version', DEFAULT_VCL_VERSION)

        self.options.setdefault(
            'location',
            os.path.join(buildout['buildout']['parts-directory'], self.name)
        )
        self.options.setdefault('verbose-headers', 'off')
        self.options.setdefault('saint-mode', 'off')
        self.options.setdefault('balancer', 'none')
        self.options.setdefault('backends', '127.0.0.1:8080')
        self.options.setdefault(
            'config-file',
            os.path.join(self.options['location'], 'varnish.vcl')
        )
        self.options.setdefault('connect-timeout', '0.4s')
        self.options.setdefault('first-byte-timeout', '300s')
        self.options.setdefault('between-bytes-timeout', '60s')
        self.options.setdefault('purge-hosts', '')
        self.options.setdefault('cookie-pass', COOKIE_PASS_DEFAULT)
        self.options.setdefault('cookie-whitelist', COOKIE_WHITELIST_DEFAULT)
        # set and test for valid bind value
        self.options.setdefault('bind', '127.0.0.1:8000')
        self._process_bind()

    def _process_backends(self):
        result = []
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
                if len(raw_backend) == 3:
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

    def install(self):
        if 'configuration-file' not in self.options:
            if not os.path.exists(self.options['location']):
                os.mkdir(self.options['location'])
                self.options.created(self.options['location'])
            self.options['configuration-file'] = os.path.join(
                self.options['location'],
                'varnish.vcl'
            )
        self.create_varnish_configuration()
        return self.options.created()

    def update(self):
        self.install()

    def create_varnish_configuration(self):
        major_version = self.options['varnish_version'][0]
        minor_version = self.options['varnish_version'][-1]
        config = {}

        config['version'] = major_version

        # Preparing for new releases of VCL versions, default is 'vcl 4.0'
        config['vcl_version'] = self.options.get(
            'vcl-version',
            DEFAULT_VCL_VERSION
        )

        # We use to define the use of the standard purge
        # module from varnish 5.2, See:
        # https://varnish-cache.org/docs/5.2/whats-new/changes-5.2.html#vmod-purge
        config['minor_version'] = minor_version

        # enable verbose varnish headers
        config['verbose'] = self.options['verbose-headers'] == 'on'

        # Deprecated; see https://www.varnish-cache.org/forum/topic/2777
        # config['saint'] = self.options['saint-mode'] == 'on'
        # if config['saint'] and config['verbose']:
        #     self._log_and_raise(
        #         'When using saint-mode verbose headers must be off'
        #     )
        config['gracehealthy'] = self.options.get('grace-healthy', None)
        config['gracesick'] = self.options.get('grace-sick', '600s')

        # fixup cookies for better plone caching
        config['cookiewhitelist'] = [
            _.strip() for _ in self.options['cookie-whitelist'].split()
        ]
        config['cookiepass'] = []
        for line in self.options['cookie-pass'].split():
            line = line.strip()
            if not line:
                continue
            match = COOKIE_PASS_RE.match(line)
            mg = match.groups()
            if not mg and len(mg) != 2:
                continue
            config['cookiepass'].append(
                dict(zip(('match', 'exclude'), mg))
            )
        # inject custom vcl
        config['custom'] = {}
        for name in ('vcl_recv', 'vcl_hit', 'vcl_miss',
                     'vcl_backend_fetch', 'vcl_purge', 'vcl_deliver',
                     'vcl_pipe', 'vcl_backend_response', 'vcl_hash'):
            config['custom'][name] = self.options.get(name, '')

        config['backends'] = self._process_backends()
        config['directors'] = self._process_balancers(
            self.options['balancer'].strip(),
            config['backends']
        )
        config['zope2_vhm_map'] = self._process_zope_vhm_map(
            config['backends']
        )
        config['code404page'] = True

        # build the purge host string
        config['purgehosts'] = set([])
        for segment in self.options['purge-hosts'].split():
            segment = segment.strip()
            if segment:
                config['purgehosts'].add(segment)

        vclgenerator = VclGenerator(config)
        filedata = vclgenerator()
        with open(self.options['configuration-file'], 'wt') as fio:
            fio.write(filedata)
        self.options.created(self.options['configuration-file'])


class ScriptRecipe(BaseRecipe):

    def __init__(self, buildout, name, options):
        super(ScriptRecipe, self).__init__(buildout, name, options)

        self.options.setdefault('build-part', 'varnish-build')
        self.options.setdefault('configuration-part', 'varnish-configuration')

        self.options.setdefault(
            'varnish_version',
            self.get_from_section(
                self.options['build-part'],
                'varnish_version',
                DEFAULT_VERSION
            )
        )

        self.options.setdefault(
            'daemon',
            self.get_from_section(
                self.options['build-part'],
                'location',
                '/usr'
            ) + '/sbin/varnishd'
        )

        self.options.setdefault(
            'bind',
            self.get_from_section(
                self.options['configuration-part'],
                'bind',
                '127.0.0.1:8000'
            )
        )
        self.options.setdefault(
            'configuration-file',
            self.get_from_section(
                self.options['configuration-part'],
                'config-file',
                ''
            )
        )
        if not self.options['configuration-file']:
            self._log_and_raise('No configuration file found')
        self._process_bind()

        self.options.setdefault(
            'location',
            os.path.join(buildout['buildout']['parts-directory'], self.name)
        )
        self.options.setdefault('cache-type', 'file')
        self.options.setdefault('cache-size', '256M')
        self.options.setdefault('runtime-parameters', '')
        self.options.setdefault('secret-file', 'nosecret')
        self.options.setdefault('script-filename', os.path.join(
            self.buildout['buildout']['bin-directory'],
            self.name
        ))

    def install(self):
        if 'cache-location' not in self.options:
            if not os.path.exists(self.options['location']):
                os.mkdir(self.options['location'])
                self.options.created(self.options['location'])
            self.options['cache-location'] = os.path.join(
                self.options['location'],
                'storage'
            )
            if not os.path.exists(self.options['cache-location']):
                os.mkdir(self.options['cache-location'])
                self.options.created(self.options['cache-location'])

        script = self.create_varnish_script()
        with open(self.options['script-filename'], 'wt') as fio:
            fio.write(script)
        os.chmod(self.options['script-filename'], 0o755)
        self.options.created(self.options['script-filename'])
        return self.options.created()

    def create_varnish_script(self):
        # render script file
        data = {}
        data['version'] = self.options['varnish_version']
        data['daemon'] = self.options['daemon']
        data['user'] = self.options.get('user')
        data['group'] = self.options.get('group')
        data['cfg_file'] = self.options['configuration-file']
        data['pid_file'] = os.path.join(
            self.options['location'], 'varnish.pid')
        data['bind'] = self.options['bind']
        data['cache_type'] = self.options['cache-type'].lower()
        data['cache_location'] = self.options['cache-location']
        data['cache_size'] = self.options['cache-size']
        data['mode'] = self.options.get('mode', 'daemon')
        data['name'] = self.options.get('name')
        data['secret'] = self.options.get('secret-file', 'nosecret').lower()
        data['telnet'] = self.options.get('telnet')
        data['parameters'] = self.options['runtime-parameters'].strip().split()

        template = jinja2env.get_template('start_script.jinja2')
        return template.render(data)
