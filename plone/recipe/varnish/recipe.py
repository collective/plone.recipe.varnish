# -*- coding: utf-8 -*-
from jinja2 import Environment
from jinja2 import PackageLoader
import logging
import os
import zc.buildout


CONFIG_EXCLUDES = set(['zope2_vhm_map', 'zope2_vhm_port', 'zope2_vhm_ssl',
                       'zope2_vhm_ssl_port', 'backends', 'verbose-headers',
                       'saint-mode', ])

jinja2env = Environment(
    loader=PackageLoader('plone.recipe.varnish', 'templates')
)
TEMPLATES_BY_MAJORVERSION = {
    '3': jinja2env.get_template('varnish4.vcl.jinja2'),
    '4': jinja2env.get_template('varnish4.vcl.jinja2'),
}

BALANCER_TYPES = [
    'round-robin',
    'random',
]


# below here tpl unused since jinja 2

VCL_FETCH_VERBOSE_V3 = '''\
    # Varnish determined the object was not cacheable
    if (beresp.ttl <= 0s) {
        set beresp.http.X-Cacheable = "NO:Not Cacheable";

    # You don't wish to cache content for logged in users
    } elsif (req.http.Cookie ~ "(UserID|_session)") {
        set beresp.http.X-Cacheable = "NO:Got Session";
        return(hit_for_pass);

    # You are respecting the Cache-Control=private header from the backend
    } elsif (beresp.http.Cache-Control ~ "private") {
        set beresp.http.X-Cacheable = "NO:Cache-Control=private";
        return(hit_for_pass);

    # Varnish determined the object was cacheable
    } else {
        set beresp.http.X-Cacheable = "YES";
    }
'''

VCL_FETCH_SAINT = '''
    if (beresp.status >=500 && beresp.status < 600) {
        set beresp.saintmode = 10s;
        return(hit_for_pass);
      }
'''

VCL_DELIVER_VERBOSE = '''\
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
'''
VCL_PLONE_COOKIE_FIXUP = '''\
        if (req.http.Cookie && req.http.Cookie ~ "__ac(|_(name|password|persistent))=") {
                if (req.url ~ "\.(js|css|kss)") {
                        remove req.http.cookie;
                        return(lookup);
                }
                return(pass);
        }
        return(pass);
    }
    if (req.http.Cookie) {
        set req.http.Cookie = ";"%(str_concat)sreq.http.Cookie;
        set req.http.Cookie = regsuball(req.http.Cookie, "; +", ";");
        set req.http.Cookie = regsuball(req.http.Cookie, ";(statusmessages|__ac|_ZopeId|__cp)=", "; \1=");
        set req.http.Cookie = regsuball(req.http.Cookie, ";[^ ][^;]*", "");
        set req.http.Cookie = regsuball(req.http.Cookie, "^[; ]+|[; ]+$", "");

        if (req.http.Cookie == "") {
            remove req.http.Cookie;
        }
    }
'''




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
        self.options.setdefault('varnish_version', '3')
        if self.options['varnish_version'] == '3':
            url = 'http://repo.varnish-cache.org/source/varnish-3.0.6.tar.gz'
        else:
            url = 'http://repo.varnish-cache.org/source/varnish-2.1.5.tar.gz'
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
        zc.buildout.UserError(message)

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
        backends = [
            x.rsplit(':', 2)
            for x in self.options['backends'].strip().split()
        ]

        # consistency checks
        if len(backends) > 1:
            lengths = set([len(x) for x in backends])
            if lengths != set([3]):
                self._log_and_raise(
                    'When using multiple backends a hostname '
                    'must be given for each client'
                )
            else:
                hostnames = [x[0] for x in backends]
                if len(hostnames) != len(set(hostnames)) \
                   and balancer[0] == 'none':
                    self._log_and_raise(
                        'When using multiple backends for the same hostname '
                        'you must define a balancer'
                    )
        return backends

    def _process_zope_vhm_map(self, backends):
        zope2_vhm_map = {}
        for line in self.options.get('zope2_vhm_map', '').split():
            key, value = line.split(':')
            zope2_vhm_map[key] = value

        # consistency checks
        if zope2_vhm_map:
            lengths = set([len(x) for x in backends])
            if lengths != set([3]):
                self._log_and_raise(
                    'When using VHM a hostname must be given for each backend'
                )
        return zope2_vhm_map

    def createVarnishConfig(self):
        major_version = self.options['varnish_version']
        if major_version not in TEMPLATES_BY_MAJORVERSION:
            self._log_and_raise(
                'Varnish version must be one of {0}'
                'Use an older version of this recipe to support older '
                'Varnish. Newer versions than listed here are not '
                'supported.'.format(str(TEMPLATES_BY_MAJORVERSION.keys()))
            )
        config = {}
        config['version'] = major_version

        balancer = self.options['balancer'].strip().split()
        backends = config['backends'] = self._process_backends()
        zope2_vhm_map = self._process_zope_vhm_map(backends)

        # generate vcl director config if we are load balancing
        config['directors'] = list()

        # we are prepared to support mutliple directors, but for now
        # this is not implemented
        if balancer[0] in BALANCER_TYPES:
            director = dict()
            director['type'] = balancer[0]
            director['backends'] = [_['name'] for _ in backends]
            config['directors'].append(director)
        elif balancer[0] != 'none':
            self._log_and_raise(
                'balancer type {0} not supported.'.format(balancer[0])
            )

        # collect already configure vhostings
        config['purgehosts'] = set()
        config['vhosting'] = list()
        config['404page'] = False

        vhosting_configured = set()

        # configure all backends
        for idx, backend in enumerate(backends):
            vh = dict()
            config['vhosting'].append(vh)
            vh['name'] = 'backend_{0:03d}'.format(idx)
            vh['lines'] = []
            url = None
            try:
                if len(backend) == 3:
                    url, ip, port = backend
                else:
                    ip, port = backend
            except ValueError:
                self._log_and_raise(
                    'Invalid syntax for backend: {0}'.format(
                        ':'.join(backend)
                    )
                )
                raise zc.buildout.UserError('Invalid syntax for backends')

            # collect ips allowed for purging
            config['purgehosts'].add(ip)

            # vcl backend config base
            vh['host'] = ip
            vh['port'] = port
            vh['connect_timeout'] = self.options['connect-timeout']
            vh['first_byte_timeout'] = self.options['first-byte-timeout']
            vh['between_bytes_timeout'] = self.options['between-bytes-timeout']

            # set backend if not using virtual hosting
            if not url:
                vh['match'] = None
                if balancer[0] != 'none':
                    vh['backend'] = 'director_0'
                else:
                    vh['backend'] = 'backend_{0:03d}'.format(0)

            # set backed based on virtual hosting options
            else:
                if url in vhosting_configured:
                    # dup
                    continue

                # set backend based on path only
                if url[0] in '/:':
                    path = url.lstrip(':/')
                    vh['match'].append(
                        'req.url ~ "^/{0}"'.format(path)
                    )
                    vh['lines'].append(
                        'set req.http.host = "{0}";'.format(
                            url.split(':')[0].split('/').pop()
                        )
                    )

                # set backend based on hostname and path
                elif url.find(':') != -1:
                    hostname, path = url.split(':', 1)
                    vh['match'] = (
                        'req.http.host ~ "^[{0}](:[0-9]+)?$" && '
                        'req.url ~ "^/{1}"'.format(
                            hostname,
                            path.lstrip(':/')
                        )
                    )

                # set backend based on hostname
                else:
                    vh['match'] = 'req.http.host ~ "^{0}(:[0-9]+)?$"'.format(
                        url
                    )

                # translate into vhm url if defined for hostname
                if url in zope2_vhm_map:
                    location = zope2_vhm_map[url].lstrip('/')
                    external_port = self.options.get(
                        'zope2_vhm_port',
                        self.options['bind-port']
                    )
                    proto = 'http'
                    if self.options.get('zope2_vhm_ssl', False) == 'on':
                        external_port = self.options.get(
                            'zope2_vhm_ssl_port', '443'
                        )
                        proto = 'https'
                    vh['lines'].append(
                        'set req.url = "/VirtualHostBase/{0}/{1}:{2}/{3}/'
                        'VirtualHostRoot"{4}req.url;'.format(
                            proto, url, external_port, location, str_concat
                        )
                    )

                # set backend for the request
                if balancer[0] != 'none':
                    vh['backend'] = 'director_0'
                else:
                    vh['backend'] = 'backend_{0:d}'.format(idx)

                vhosting_configured.add(url)

        if len(backends[0]) == 3:
            config['404page'] = True

        #build the purge host string
        for segment in self.options['purge-hosts'].split():
            segment = segment.strip()
            if segment:
                config['purgehosts'].add(segment)

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

        # render vcl file
        template = TEMPLATES_BY_MAJORVERSION[major_version]
        with open(self.options['config'], 'wt') as fio:
            fio.write(template.render(**config))
        self.options.created(self.options['config'])
