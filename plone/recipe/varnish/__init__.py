import logging
import os
import string
import sys

import zc.buildout


verbose_headers = {
    # key: (value, indentation)
    # 'header_hit_notcacheable': ('PASS (not cacheable - hit)', 8),
    # 'header_hit_deliver': ('HIT (deliver - from cache)', 4),
    'header_fetch_notcacheable': ('FETCH (pass - not cacheable)', 8),
    'header_fetch_setcookie': ('FETCH (pass - response sets cookie)', 8),
    'header_fetch_cachecontrol': ('FETCH (pass - cache control disallows)', 8),
    'header_fetch_auth': ('FETCH (pass - authorized and no public cache control)', 8),
    'header_fetch_insert': ('FETCH (insert)', 4),
}
headertpl = '\n%sset obj.http.X-Varnish-Action = "%s";'

config_excludes = set(["zope2_vhm_map", "backends", "verbose-headers"])


class ConfigureRecipe:

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout
        self.logger = logging.getLogger(self.name)

        self.options["location"] = os.path.join(
                buildout["buildout"]["parts-directory"], self.name)

        # Expose the download url of a known-good Varnish release
        url = "http://downloads.sourceforge.net/project/varnish/varnish/2.1/varnish-2.1.tar.gz"
        self.options.setdefault("download-url", url)

        # Set some default options
        self.options.setdefault("bind", "127.0.0.1:8000")
        self.daemon = self.options["daemon"]
        self.options.setdefault("cache-size", "1G")
        self.options.setdefault("runtime-parameters", "")
        if "config" in self.options:
            if set(self.options.keys()).intersection(config_excludes):
                msg = ("When config= option is specified the following "
                       "options cant be used: ")
                msg += ' '.join(config_excludes)
                self.logger.error(msg)
                raise zc.buildout.UserError(msg)
            self.options["generate_config"] = "false"
        else:
            self.options["generate_config"] = "true"
            self.options.setdefault('verbose-headers', 'off')
            self.options.setdefault("balancer", "none")
            self.options.setdefault("backends", "127.0.0.1:8080")
            self.options["config"] = os.path.join(self.options["location"],
                                                  "varnish.vcl")
        self.options.setdefault("connect-timeout", "0.4s")
        self.options.setdefault("first-byte-timeout", "300s")
        self.options.setdefault("between-bytes-timeout", "60s")

        # Test for valid bind value
        self.options["bind"] = self.options.get("bind").lstrip(":")
        bind=self.options["bind"].split(":")
        if len(bind)==1 and bind[0].isdigit():
            self.options["bind-host"]=''
            self.options["bind-port"]=bind[0]
            self.options["bind"]=':' + bind[0]
        elif len(bind)==2 and bind[1].isdigit():
            self.options["bind-host"]=bind[0]
            self.options["bind-port"]=bind[1]
        else:
            self.logger.error("Invalid syntax for bind")
            raise zc.buildout.UserError("Invalid syntax for bind")

    def install(self):
        location=self.options["location"]

        if not os.path.exists(location):
            os.mkdir(location)
        self.options.created(location)

        self.addVarnishRunner()
        if self.options["generate_config"]=="true":
            self.createVarnishConfig()

        return self.options.created()

    def update(self):
        pass

    def addVarnishRunner(self):
        target = os.path.join(self.buildout["buildout"]["bin-directory"], self.name)
        f = open(target, "wt")

        parameters = self.options['runtime-parameters'].strip().split()

        print >>f, "#!/bin/sh"
        print >>f, "exec %s \\" % self.daemon
        if "user" in self.options:
            print >>f, '    -p user=%s \\' % self.options["user"]
        if "group" in self.options:
            print >>f, '    -p group=%s \\' % self.options["group"]
        print >>f, '    -f "%s" \\' % self.options["config"]
        print >>f, '    -P "%s" \\' % \
                os.path.join(self.options["location"], "varnish.pid")
        print >>f, '    -a %s \\' % self.options["bind"]
        if self.options.get("telnet", None):
            print >>f, '    -T %s \\' % self.options["telnet"]
        print >>f, '    -s file,"%s",%s \\' % (
                os.path.join(self.options["location"], "storage"),
                self.options["cache-size"])
        if self.options.get("mode", "daemon") == "foreground":
            print >>f, '    -F \\'
        for parameter in parameters:
            print >>f, '    -p %s \\' % (parameter)
        print >>f, '    "$@"'
        f.close()
        os.chmod(target, 0755)
        self.options.created(target)

    def createVarnishConfig(self):
        module = ''
        for x in self.options["recipe"]:
            if x in (':', '>', '<', '='):
                break
            module += x

        whereami=sys.modules[module].__path__[0]
        template=open(os.path.join(whereami, "template.vcl")).read()
        template=string.Template(template)
        config={}

        zope2_vhm_map=self.options.get("zope2_vhm_map", "").split()
        zope2_vhm_map=dict([x.split(":") for x in zope2_vhm_map])

        balancer = self.options["balancer"].strip().split()

        backends=self.options["backends"].strip().split()
        backends=[x.rsplit(":", 2) for x in backends]
        if len(backends)>1:
            lengths=set([len(x) for x in backends])
            if lengths!=set([3]):
                self.logger.error("When using multiple backends a hostname "
                                  "must be given for each client")
                raise zc.buildout.UserError("Multiple backends without hostnames")

        output=""
        purgehosts=set([])
        vhosting=""
        director='director director_0 '
        # set up director if we are load balancing
        if (balancer[0] != "none"):
            if (balancer[0] == "round-robin"):
                director+='round-robin {\n'
            elif (balancer[0] == "random"):
                director+='random {\n'

        for i in range(len(backends)):
            parts=backends[i]
            output+='backend backend_%d {\n' % i

            # no hostname or path, so we have only one backend
            if len(parts)==2:
                output+='\t.host = "%s";\n' % parts[0]
                output+='\t.port = "%s";\n' % parts[1]
                # if we are configuring a load balancer, set up the director as the backend
                if (balancer[0] != 'none'):
                    vhosting='set req.backend = director_0;'
                    if (balancer[0] == 'round-robin'):
                        director+='\t{\n\t\t.backend = backend_%d;\n\t}\n' % i
                    elif (balancer[0] == 'random'):
                        director+='\t{\n\t\t.backend = backend_%d; .weight = 1;\n\t}\n' % i
                else:
                    vhosting='set req.backend = backend_0;'
                    output+='\t.connect_timeout = %s;\n' % self.options["connect-timeout"]
                    output+='\t.first_byte_timeout = %s;\n' % self.options["first-byte-timeout"]
                    output+='\t.between_bytes_timeout = %s;\n' % self.options["between-bytes-timeout"]


                #add a host to the set to enable purge requests being allowed
                purgehosts.add(parts[0])


            #hostname and/or path is defined, so we may have multiple backends
            elif len(parts)==3:
                output+='.host = "%s";\n' % parts[1]
                output+='.port = "%s";\n' % parts[2]
                if (balancer[0] == 'none'):
                    output+='.connect_timeout = %s;\n' % self.options["connect-timeout"]
                    output+='.first_byte_timeout = %s;\n' % self.options["first-byte-timeout"]
                    output+='.between_bytes_timeout = %s;\n' % self.options["between-bytes-timeout"]

                #add a host to the set to enable purge requests being allowed
                purgehosts.add(parts[1])

                # set backend based on path
                if parts[0].startswith('/') or parts[0].startswith(':'):
                    path=parts[0].lstrip(':/')
                    vhosting+='elsif (req.url ~ "^/%s") {\n' % path
                    vhosting+='\tset req.http.host = "%s";\n' % parts[0].split(':')[0].split('/').pop()

                # set backend based on hostname and path
                elif parts[0].find(':') != -1:
                    hostname, path = parts[0].split(':', 1)
                    path=path.lstrip(':/')
                    vhosting+='elsif (req.http.host ~ "^%s(:[0-9]+)?$" && req.url ~ "^/%s") {\n' \
                                % (hostname, path)

                    vhosting+='\tset req.backend = backend_%d;\n' % i

                # set backend based on hostname
                else:
                    vhosting+='elsif (req.http.host ~ "^%s(:[0-9]+)?$") {\n' \
                                % parts[0]

                    # translate into vhm url if defined for hostname
                    if parts[0] in zope2_vhm_map:
                        location=zope2_vhm_map[parts[0]]
                        if location.startswith("/"):
                            location=location[1:]
                        vhosting+='\tset req.url = "/VirtualHostBase/http/%s:%s/%s/VirtualHostRoot" req.url;\n' \
                                       % (parts[0], self.options["bind-port"], location)

                if (balancer[0] != 'none'):
                    vhosting+='\tset req.backend = director_0;\n'
                    if (balancer[0] == 'round-robin'):
                        director+='\t{\n\t\t.backend = backend_%d;\n\t}\n' % i
                    elif (balancer[0] == 'random'):
                        director+='\t{\n\t\t.backend = backend_%d; .weight = 1;\n\t}\n' % i
                else:
                    vhosting+='\tset req.backend = backend_%d;\n' % i

                vhosting+='}\n'

            else:
                self.logger.error("Invalid syntax for backend: %s" %
                                        ":".join(parts))
                raise zc.buildout.UserError("Invalid syntax for backends")
            output+="}\n"

        director+='}\n'

        if len(backends[0])==3:
            vhosting=vhosting[3:]
            vhosting+='else {\n'
            vhosting+='\terror 404 "Unknown virtual host";\n'
            vhosting+='}'
            vhosting="\t".join(vhosting.splitlines(1))

        #build the purge host string
        purge=""
        for host in purgehosts:
            purge+='\t"%s";\n' % host

        config["backends"]=output
        config["purgehosts"]=purge
        config["virtual_hosting"]=vhosting
        if (balancer[0] != 'none'):
            config["director"]=director
        else:
            config["director"]=''
        for key in verbose_headers:
            if self.options['verbose-headers'] == 'on':
                pair = verbose_headers[key][1] * ' ', verbose_headers[key][0]
                config[key] = headertpl % pair
            else:
                config[key] = ''

        f=open(self.options["config"], "wt")
        f.write(template.safe_substitute(config))
        f.close()
        self.options.created(self.options["config"])
