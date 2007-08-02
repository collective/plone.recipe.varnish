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


class Recipe:
    def __init__(self, buildout, name, options):
        self.name=name
        self.options=options
        self.buildout=buildout
        self.logger=logging.getLogger(self.name)

        self.svn=options.get("svn", None)
        self.url=options.get("url", None)
        if not (self.svn or self.url):
            self.logger.error("You need to specify either a URL or subversion repository")
            raise zc.buildout.UserError("No download location given")

        options["location"] = os.path.join(
                buildout["buildout"]["parts-directory"], self.name)

        options["source-location"]=os.path.join(self.options["location"], "source")
        options["binary-location"]=os.path.join(self.options["location"], "install")

        buildout['buildout'].setdefault(
                'download-directory',
                os.path.join(buildout['buildout']['directory'], 'downloads'))


    def writeVarnishConfig(self):
        location=os.path.join(self.options["location"], "bin")


    def downloadVarnish(self):
        download_dir=self.buildout['buildout']['download-directory']

        if os.path.exists(self.options["source-location"]):
            shutil.rmtree(self.options["source-location"])
        os.mkdir(self.options["source-location"])

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


    def compileVarnish(self):
        os.chdir(self.options["source-location"])
        self.logger.info("Compiling Varnish")
        assert subprocess.call(["./configure", "--prefix=" + self.options["binary-location"]]) == 0
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


    def addVarnishRunner(self):
        target=os.path.join(self.buildout["buildout"]["bin-directory"], "varnishd")
        f=open(target, "wt")
        print >>f, "#!/bin/sh"
        print >>f, "exec %s \\" % os.path.join(
                        self.options["binary-location"], "sbin", "varnishd")
        print >>f, '    -f "%s" \\' % os.path.join(
                            self.options["binary-location"], "varnish.vcl")
        print >>f, '    -a %s \\' % self.options.get("bind", "127.0.0.1:6781")
        if self.options.get("telnet", None):
            print >>f, '    -T %s \\' % self.options["telnet"]
        print >>f, '    -s file,"%s",%s \\' % (
                os.path.join(self.options["binary-location"],
                            "var", "varnish", "storage"),
                self.options.get("cache-size", "1G"))
        print >>f, '    "$@"'
        f.close()
        os.chmod(target, 0755)
        self.options.created(target)


    def createVarnishConfig(self):
        whereami=sys.modules[self.options["recipe"]].__path__[0]
        template=open(os.path.join(whereami, "template.vcl")).read()
        template=string.Template(template)
        config={}
        parts=self.options.get("backend", "127.0.0.1:8080").strip().split(":")
        config["backend_host"]=parts[0]
        if len(parts)==2:
            config["backend_port"]=parts[1]
        else:
            config["backend_port"]="8080"

        target=os.path.join(self.options["binary-location"], "varnish.vcl")
        f=open(target, "wt")
        f.write(template.safe_substitute(config))
        f.close()


    def install(self):
        location=self.options["location"]
        if os.path.exists(location):
            shutil.rmtree(location)
        os.mkdir(location)

        self.options.created(location)

        self.downloadVarnish()
        self.compileVarnish()
        self.addScriptWrappers()
        self.addVarnishRunner()
        self.createVarnishConfig()

        return self.options.created()


    def update(self):
        pass


