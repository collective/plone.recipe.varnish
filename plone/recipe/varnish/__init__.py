import logging
import os
import setuptools
import shutil
import string
import sys
import subprocess
import tempfile
import urllib2
import urlparse
import zc.buildout

OSX = sys.platform.startswith('darwin')


class BuildRecipe:
    def __init__(self, buildout, name, options):
        self.name=name
        self.options=options
        self.buildout=buildout
        self.logger=logging.getLogger(self.name)

        self.svn=options.get("svn", None)
        self.url=options.get("url", None)
        if not (self.svn or self.url):
            self.logger.error(
                    "You need to specify either a URL or subversion repository")
            raise zc.buildout.UserError("No download location given")

        location=options["location"]=os.path.join(
                buildout["buildout"]["parts-directory"], self.name)
        options["source-location"]=os.path.join(location, "source")
        options["binary-location"]=os.path.join(location, "install")
        options["daemon"]=os.path.join(options["binary-location"], "varnishd")

        # Set some default options
        buildout['buildout'].setdefault(
                'download-directory',
                os.path.join(buildout['buildout']['directory'], 'downloads'))


    def install(self):
        location=self.options["location"]
        if not os.path.exists(location):
            os.mkdir(location)
        self.options.created(location)

        self.downloadVarnish()
        self.compileVarnish()
        self.addScriptWrappers()

        return self.options.created()


    def update(self):
        pass


    def downloadVarnish(self):
        download_dir=self.buildout['buildout']['download-directory']

        if os.path.exists(self.options["source-location"]):
            shutil.rmtree(self.options["source-location"])

        if self.svn:
            self.logger.info("Checking out varnish from subversion.")
            assert os.system("svn co %s %s" % (self.options["svn"], self.options["source-location"]))==0
        else:
            self.logger.info("Downloading varnish tarball.")
            if not os.path.isdir(download_dir):
                os.mkdir(download_dir)

            _, _, urlpath, _, _, _ = urlparse.urlparse(self.url)
            tmp=tempfile.mkdtemp("buildout-"+self.name)

            try:
                fname=os.path.join(download_dir, urlpath.split("/")[-1])
                if not os.path.exists(fname):
                    f=open(fname, "wb")
                    try:
                        f.write(urllib2.urlopen(self.url).read())
                    except:
                        os.remove(fname)
                        raise
                    f.close()

                setuptools.archive_util.unpack_archive(fname, tmp)

                files=os.listdir(tmp)
                shutil.move(os.path.join(tmp, files[0]), self.options["source-location"])
            finally:
                shutil.rmtree(tmp)


    def patchForOSX(self):
        """Patch libtool on OS X.
        
        workaround for http://varnish.projects.linpro.no/ticket/118
        """
        libtool_file_name = os.path.join(self.options["source-location"], 'libtool')
        libtool_source = open(libtool_file_name, 'r').read()
        libtool_source = libtool_source.replace('export_dynamic_flag_spec=""', 
                                                'export_dynamic_flag_spec="-flat_namespace"')
        open(libtool_file_name, 'w').write(libtool_source)


    def compileVarnish(self):
        os.chdir(self.options["source-location"])
        self.logger.info("Compiling Varnish")
        
        if self.svn:
            assert subprocess.call(["./autogen.sh"]) == 0
        
        assert subprocess.call(["./configure", "--prefix=" + self.options["binary-location"]]) == 0
        
        if OSX:
            self.PatchForOSX()
        
        assert subprocess.call(["make", "install"]) == 0


    def addScriptWrappers(self):
        bintarget=self.buildout["buildout"]["bin-directory"]

        for dir in ["bin", "sbin"]:
            dir=os.path.join(self.options["binary-location"], dir)
            for file in os.listdir(dir):
                self.logger.info("Adding script wrapper for %s" % file)
                target=os.path.join(bintarget, file)
                f=open(target, "wt")
                print >>f, "#!/bin/sh"
                print >>f, 'exec %s "$@"' % os.path.join(dir, file)
                f.close()
                os.chmod(target, 0755)
                self.options.created(target)


class ConfigureRecipe:
    def __init__(self, buildout, name, options):
        self.name=name
        self.options=options
        self.buildout=buildout
        self.logger=logging.getLogger(self.name)

        # Set some default options
        self.options["bind"]=self.options.get("bind", "127.0.0.1:8000")
        self.options["cache-size"]=self.options.get("cache-size", "1G")
        self.options["backends"]=self.options.get("backends", "127.0.0.1:8080")
        self.options["user"]=self.options.get("user", "nobody")
        self.options["group"]=self.options.get("group", "")
        self.options["daemon"]=self.options.get("daemon", 
                os.path.join(buildout["buildout"]["bin-directory"], "varnishd"))

        # Convenience settings
        (host,port)=self.options["bind"].split(":")
        self.options["bind-host"]=host
        self.options["bind-port"]=port
        options["location"] = os.path.join(
                buildout["buildout"]["parts-directory"], self.name)


    def install(self):
        location=self.options["location"]
        if not os.path.exists(location):
            os.mkdir(location)
        self.options.created(location)

        self.addVarnishRunner()
        self.createVarnishConfig()

        return self.options.created()


    def update(self):
        pass


    def addVarnishRunner(self):
        target=os.path.join(self.buildout["buildout"]["bin-directory"],
                                self.name)
        f=open(target, "wt")
        print >>f, "#!/bin/sh"
        print >>f, "exec %s \\" % self.options["daemon"]
        print >>f, '    -p user=%s \\' % self.options["user"]
        if self.options["group"]:
            print >>f, '    -p group=%s \\' % self.options["group"]
        print >>f, '    -f "%s" \\' % os.path.join(
                            self.options["location"], "varnish.vcl")
        print >>f, '    -a %s \\' % self.options["bind"]
        if self.options.get("telnet", None):
            print >>f, '    -T %s \\' % self.options["telnet"]
        print >>f, '    -s file,"%s",%s \\' % (
                os.path.join(self.options["location"], "storage"),
                self.options["cache-size"])
        print >>f, '    "$@"'
        f.close()
        os.chmod(target, 0755)
        self.options.created(target)


    def createVarnishConfig(self):
        module=self.options["recipe"].split(":")[0]
        whereami=sys.modules[module].__path__[0]
        template=open(os.path.join(whereami, "template.vcl")).read()
        template=string.Template(template)
        config={}

        zope2_vhm_map=self.options.get("zope2_vhm_map", "").split()
        zope2_vhm_map=dict([x.split(":") for x in zope2_vhm_map])

        backends=self.options["backends"].strip().split()
        backends=[x.split(":") for x in backends]
        if len(backends)>1:
            lengths=set([len(x) for x in backends])
            if lengths!=set([3]):
                self.logger.error("When using multiple backends a hostname "
                                  "must be given for each client")
                raise zc.buildout.UserError("Multiple backends without hostnames")


        output=""
        vhosting=""
        for i in range(len(backends)):
            parts=backends[i]
            output+='backend backend_%d {\n' % i
            if len(parts)==2:
                output+='    set backend.host = "%s";\n' % parts[0]
                output+='    set backend.port = "%s";\n' % parts[1]
            elif len(parts)==3:
                output+='    set backend.host = "%s";\n' % parts[1]
                output+='    set backend.port = "%s";\n' % parts[2]
                vhosting+=' elsif (req.http.host ~ "^%s(:[0-9]+)?$") {\n' % parts[0]
                vhosting+='    set req.backend = backend_%d;\n' % i
                if parts[0] in zope2_vhm_map:
                    location=zope2_vhm_map[parts[0]]
                    if location.startswith("/"):
                        location=location[1:]
                    vhosting+='    set req.url = regsub(req.url, "(.*)", "/VirtualHostBase/http/%s:%s/%s/VirtualHostRoot/$1");\n' % \
                                (parts[0], self.options["bind-port"], location)
                vhosting+='}'
            else:
                self.logger.error("Invalid syntax for backend: %s" % 
                                        ":".join(parts))
                raise zc.buildout.UserError("Invalid syntax for backends")
            output+="}\n\n"


        vhosting=vhosting[4:]
        if len(backends)==0 and len(backends[0])==2:
            vhosting='set req.backend = backend_0;'
        elif len(backends[0])==3:
            vhosting+=' else {\n'
            vhosting+='    error 404 "Unknown virtual host";\n'
            vhosting+='}\n'

        config["backends"]=output
        config["virtual_hosting"]=vhosting

        target=os.path.join(self.options["location"], "varnish.vcl")
        f=open(target, "wt")
        f.write(template.safe_substitute(config))
        f.close()

