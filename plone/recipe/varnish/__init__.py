import logging
import os
import string
import sys
import zc.buildout


CONFIG_EXCLUDES = set(['zope2_vhm_map', 'zope2_vhm_port', 'zope2_vhm_ssl',
                       'zope2_vhm_ssl_port', 'backends', 'verbose-headers',
                       'saint-mode', ])

VCL_FETCH_VERBOSE_V2 = '''
    # Varnish determined the object was not cacheable
    if (!beresp.cacheable) {
        set beresp.http.X-Cacheable = "NO:Not Cacheable";

    # You don't wish to cache content for logged in users
    } elsif (req.http.Cookie ~ "(UserID|_session)") {
        set beresp.http.X-Cacheable = "NO:Got Session";
        return(pass);

    # You are respecting the Cache-Control=private header from the backend
    } elsif (beresp.http.Cache-Control ~ "private") {
        set beresp.http.X-Cacheable = "NO:Cache-Control=private";
        return(pass);

    # You are extending the lifetime of the object artificially
    } elsif (beresp.ttl < 1s) {
        set beresp.ttl   = 5s;
        set beresp.grace = 5s;
        set beresp.http.X-Cacheable = "YES:FORCED";

    # Varnish determined the object was cacheable
    } else {
        set beresp.http.X-Cacheable = "YES";
    }
'''
VCL_FETCH_VERBOSE_V3 = '''
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
        return(restart);
      }
'''

VCL_DELIVER_VERBOSE = '''
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
'''
VCL_PLONE_COOKIE_FIXUP = '''
    if (req.http.Cookie && req.http.Cookie ~ "__ac(|_(name|password|persistent))=") {
        if (req.url ~ "\.(js|css|kss)") {
            remove req.http.cookie;
            return(lookup);
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

class ConfigureRecipe:

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout
        self.logger = logging.getLogger(self.name)

        self.options.setdefault('location', os.path.join(
                buildout['buildout']['parts-directory'], self.name))

        # Expose the download url of a known-good Varnish release



        # Set some default options
        self.options.setdefault('varnish_version', '2')
        if self.options['varnish_version'] == '3':
            url = 'http://repo.varnish-cache.org/source/varnish-3.0.5.tar.gz'
        else:
            url = 'http://repo.varnish-cache.org/source/varnish-2.1.5.tar.gz'
        self.options.setdefault('download-url', url)
        self.options.setdefault('bind', '127.0.0.1:8000')
        self.daemon = self.options['daemon']
        self.options.setdefault('cache-type', 'file')
        self.options.setdefault('cache-location',
                                os.path.join(self.options['location'], 'storage'))
        self.options.setdefault('cache-size', '256M')
        self.options.setdefault('runtime-parameters', '')
        if 'config' in self.options:
            if set(self.options.keys()).intersection(CONFIG_EXCLUDES):
                msg = ('When config= option is specified the following '
                       'options cant be used: ')
                msg += ' '.join(config_excludes)
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
        bind=self.options['bind'].split(':')
        if len(bind)==1 and bind[0].isdigit():
            self.options['bind-host']=''
            self.options['bind-port']=bind[0]
            self.options['bind']=':' + bind[0]
        elif len(bind)==2 and bind[1].isdigit():
            self.options['bind-host']=bind[0]
            self.options['bind-port']=bind[1]
        else:
            self.logger.error('Invalid syntax for bind')
            raise zc.buildout.UserError('Invalid syntax for bind')

    def install(self):
        location=self.options['location']

        if not os.path.exists(location):
            os.mkdir(location)
        self.options.created(location)

        self.addVarnishRunner()
        if self.options['generate_config']=='true':
            self.createVarnishConfig()

        return self.options.created()

    def update(self):
        pass

    def addVarnishRunner(self):
        target = os.path.join(self.buildout['buildout']['bin-directory'], self.name)
        f = open(target, 'wt')

        parameters = self.options['runtime-parameters'].strip().split()

        print >>f, '#!/bin/sh'
        print >>f, 'exec %s \\' % self.daemon
        if 'user' in self.options:
            print >>f, '    -p user=%s \\' % self.options['user']
        if 'group' in self.options:
            print >>f, '    -p group=%s \\' % self.options['group']
        print >>f, '    -f "%s" \\' % self.options['config']
        print >>f, '    -P "%s" \\' % \
                os.path.join(self.options['location'], 'varnish.pid')
        print >>f, '    -a %s \\' % self.options['bind']
        if self.options.get('telnet', None):
            print >>f, '    -T %s \\' % self.options['telnet']
        if self.options['cache-type'] == 'malloc':
            print >>f, '    -s %s,%s \\' % (
                    self.options['cache-type'],
                    self.options['cache-size'])
        else:
            print >>f, '    -s %s,"%s",%s \\' % (
                    self.options['cache-type'],
                    self.options['cache-location'],
                    self.options['cache-size'])
        if self.options.get('mode', 'daemon') == 'foreground':
            print >>f, '    -F \\'
        if self.options.get('name', None):
            print >>f, '    -n %s \\' % self.options['name']
        for parameter in parameters:
            print >>f, '    -p %s \\' % (parameter)
        print >>f, '    "$@"'
        f.close()
        os.chmod(target, 0755)
        self.options.created(target)

    def createVarnishConfig(self):
        module = ''
        for x in self.options['recipe']:
            if x in (':', '>', '<', '='):
                break
            module += x

        whereami = sys.modules[module].__path__[0]
        str_concat = ' '
        vcl_deliver_verbose = VCL_DELIVER_VERBOSE
        vcl_fetch_verbose = VCL_FETCH_VERBOSE_V2
        if self.options['varnish_version'] == '2':
            template = open(os.path.join(whereami, 'template.vcl')).read()
        elif self.options['varnish_version'] == '3':
            template = open(os.path.join(whereami, 'template3.vcl')).read()
            str_concat = ' + '
            vcl_fetch_verbose = VCL_FETCH_VERBOSE_V3
        else:
            raise ValueError(
                u'Unknown varnish version %s' % self.options['varnish_version'])
        template = string.Template(template)
        config = {}

        balancer = self.options['balancer'].strip().split()

        backends = self.options['backends'].strip().split()
        backends = [x.rsplit(':', 2) for x in backends]
        if len(backends)>1:
            lengths = set([len(x) for x in backends])
            if lengths != set([3]):
                self.logger.error('When using multiple backends a hostname '
                                  'must be given for each client')
                raise zc.buildout.UserError('Multiple backends without hostnames')
            else:
                hostnames = [x[0] for x in backends]
                if len(hostnames) != len(set(hostnames)) and balancer[0] == 'none':
                    self.logger.error('When using multiple backends for the same hostname '
                                      'you must define a balancer')
                    raise zc.buildout.UserError('Multiple backends without balancer')


        zope2_vhm_map = self.options.get('zope2_vhm_map', '').split()
        zope2_vhm_map = dict([x.split(':') for x in zope2_vhm_map])
        if zope2_vhm_map:
            lengths = set([len(x) for x in backends])
            if lengths != set([3]):
                self.logger.error('When using VHM a hostname must be '
                                  'given for each backend')
                raise zc.buildout.UserError('VHM backends without hostnames')

        director = ''
        backend = ''
        vhosting = ''
        purgehosts = set()
        vhosting_configured = set()

        # generate vcl director config if we are load balancing
        if (balancer[0] != 'none'):
            director += 'director director_0 '
            if (balancer[0] == 'round-robin'):
                director += 'round-robin {\n'
            elif (balancer[0] == 'random'):
                director += 'random {\n'
            for i in range(len(backends)):
                if (balancer[0] == 'round-robin'):
                   director += '\t{\n\t\t.backend = backend_%d;\n\t}\n' % i
                elif (balancer[0] == 'random'):
                   director += '\t{\n\t\t.backend = backend_%d; .weight = 1;\n\t}\n' % i
            director += '}\n'

        # configure all backends
        for i in range(len(backends)):
            (url, ip, port) = (None, None, None)
            try:
                (url, ip, port) = backends[i]
            except ValueError:
                try:
                    (ip, port) = backends[i]
                except ValueError:
                    self.logger.error('Invalid syntax for backend: %s' % ':'.join(backends[i]))
                    raise zc.buildout.UserError('Invalid syntax for backends')

            # generate vcl backend config
            backend += 'backend backend_%d {\n' % i
            backend += '\t.host = "%s";\n' % ip
            backend += '\t.port = "%s";\n' % port
            backend += '\t.connect_timeout = %s;\n' % self.options['connect-timeout']
            backend += '\t.first_byte_timeout = %s;\n' % self.options['first-byte-timeout']
            backend += '\t.between_bytes_timeout = %s;\n' % self.options['between-bytes-timeout']
            backend += '}\n'

            # allow purging from backend
            purgehosts.add(ip)

            # set backend if not using virtual hosting
            if not url:
                if (balancer[0] != 'none'):
                    vhosting = 'set req.backend = director_0;'
                else:
                    vhosting = 'set req.backend = backend_0;'

            # set backed based on virtual hosting options
            else:
                if url not in vhosting_configured:
                    # set backend based on path
                    if url.startswith('/') or url.startswith(':'):
                        path = url.lstrip(':/')
                        vhosting += 'elsif (req.url ~ "^/%s") {\n' % path
                        vhosting += '\tset req.http.host = "%s";\n' % url.split(':')[0].split('/').pop()

                    # set backend based on hostname and path
                    elif url.find(':') != -1:
                        hostname, path = url.split(':', 1)
                        path = path.lstrip(':/')
                        vhosting += 'elsif (req.http.host ~ "^%s(:[0-9]+)?$" && req.url ~ "^/%s") {\n' \
                                        % (hostname, path)

                    # set backend based on hostname
                    else:
                        vhosting += 'elsif (req.http.host ~ "^%s(:[0-9]+)?$") {\n' % url

                    # translate into vhm url if defined for hostname
                    if url in zope2_vhm_map:
                        location = zope2_vhm_map[url]
                        if location.startswith('/'):
                            location = location[1:]
                        external_port = self.options.get('zope2_vhm_port', self.options['bind-port'])
                        proto = 'http'
                        if self.options.get('zope2_vhm_ssl', False) == 'on':
                            external_port = self.options.get('zope2_vhm_ssl_port', '443')
                            proto = 'https'
                        vhosting += '\tset req.url = "/VirtualHostBase/%s/%s:%s/%s/VirtualHostRoot"%sreq.url;\n' \
                                        % (proto, url, external_port, location, str_concat)

                    # set backend for the request
                    if (balancer[0] != 'none'):
                        vhosting += '\tset req.backend = director_0;\n'
                    else:
                        vhosting += '\tset req.backend = backend_%d;\n' % i

                    vhosting += '}\n'
                    vhosting_configured.add(url)

        if len(backends[0]) == 3:
            vhosting = vhosting[3:]
            vhosting += 'else {\n'
            vhosting += '\terror 404 "Unknown virtual host";\n'
            vhosting += '}'
            vhosting = '\t'.join(vhosting.splitlines(1))

        #build the purge host string
        for segment in self.options['purge-hosts'].split():
            segment = segment.strip()
            if segment:
                purgehosts.add(segment)
        purge = ''
        for host in purgehosts:
            purge += '\t"%s";\n' % host

        config['backends'] = backend
        config['purgehosts'] = purge
        config['virtual_hosting'] = vhosting
        config['director'] = director

        # enable verbose varnish headers
        if self.options['verbose-headers'] == 'on':
            config['vcl_fetch_verbose'] = vcl_fetch_verbose
            config['vcl_deliver_verbose'] = vcl_deliver_verbose
        else:
            config['vcl_fetch_verbose'] = ''
            config['vcl_deliver_verbose'] = ''

        config['vcl_fetch_saint'] = ''
        if self.options['saint-mode'] == 'on':
            if self.options['verbose-headers'] == 'on':
                logger.error('When using saint-mode verbose headers must be off')
                raise zc.buildout.UserError('When using saint-mode verbose headers must be off')
            elif self.options['varnish_version'] != '3':
                logger.error('saint-mode is available for varnish 3 only')
                raise zc.buildout.UserError('saint-mode is available for varnish 3 only')
            else:
                config['vcl_fetch_saint'] = VCL_FETCH_SAINT

        # fixup cookies for better plone caching
        if self.options['cookie-fixup'] == 'on':
            config['vcl_plone_cookie_fixup'] = VCL_PLONE_COOKIE_FIXUP % {'str_concat': str_concat}
        else:
            config['vcl_plone_cookie_fixup'] = ''

        # inject custom vcl
        for name in ('vcl_recv', 'vcl_hit', 'vcl_miss', 'vcl_fetch', 'vcl_deliver', 'vcl_pipe'):
            config[name] = self.options.get(name, '')

        f = open(self.options['config'], 'wt')
        f.write(template.safe_substitute(config))
        f.close()
        self.options.created(self.options['config'])
