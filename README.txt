Varnish recipe for buildout
===========================

plone.recipe.varnish is a `zc.buildout`_ recipe to install `Varnish`_.

Configuring it is very simple. For example::

    [varnish]
    recipe = plone.recipe.varnish
    url = http://puzzle.dl.sourceforge.net/sourceforge/varnish/varnish-1.1.tar.gz
    bind = 127.0.0.1:8000
    backends = 127.0.0.1:8080
    cache-size = 1G

This configures a buildout part which runs Varnish to listen on 127.0.0.1:8000
for requests, using a 1 gigabyte cache and sending requests to a backend 
at 127.0.0.1:8080.

Wrappers for all the varnish commands are created in the bin directory
of your buildout.


Virtual hosting
---------------

Varnish supports virtual hosting by selecting a different backend server
based on headers on the incoming request. You can configure the backends
through the backends option::

  [varnish]
  backends =
     plone.org:127.0.0.1:8000
     plone.net:127.0.0.1:9000

This will generate a configuration which sends all traffic for the plone.org
host to a backend server running on port 8000 while all traffic for the
plone.net host is send to port 9000.

Zope hosting
------------

If you are using Zope as backend server you will need to rewrite the URL
so the Zope Virtual Host Monster can generate correct links for links in
your pages. This can be done either by a web server such as Apache or nginx
but can also be done by Varnish. This can be configured using the
**zope_vhm_map** option. Here is an example::

  [varnish]
  zope_vhm_map =
      plone.org:/plone
      plone.net:/plone

This tells us that the domain plone.org should be mapped to the location
/plone in the backend. By combing this with the information from the
**backends** option a varnish configuration will be generated that
maps URLs correctly.


Option reference
----------------

url
    URL for an archive containing the Varnish sources. Either **url** or
    **svn** has to be specified.

svn
    URL for a subversion repository containing Varnish sources. Either **url**
    or **svn** has to be specified.

cache-size
    The size of the cache.

bind
    Hostname and port on which Varnish will listen for requests. Defaults
    to 127.0.0.1:8000.

backends
    Specifies the backend or backends which will process the (uncached)
    requests. There are two ways to specify backends: using
    **hostname:backend server:backend port** or **backend server:backend
    port**. Using the first option allows you to do virtual hosting. If
    multiple backends are specified you have to use the full form including
    the (virtual) hostname. Defaults to 127.0.0.1:8080.

zope_vhm_map
    Defines a virtual host mapping for Zope servers. This is a list of
    **hostname:ZODB location** entries which specify the location inside
    Zope where the website for a virtual host lives.

telnet
    If specified sets the hostname and port on which Varnish will listen
    for commands using its telnet interface.


.. _Varnish: http://varnish.projects.linpro.no/
.. _zc.buildout: http://cheeseshop.python.org/pypi/zc.buildout

