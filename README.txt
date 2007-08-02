Varnish recipe for buildout
===========================

plone.recipe.varnish is a `zc.buildout`_ recipe to install `Varnish`_.

Configuring it is very simple. For example::

    [varnish]
    recipe = plone.recipe.varnish
    url = http://puzzle.dl.sourceforge.net/sourceforge/varnish/varnish-1.1.tar.gz
    bind = 127.0.0.1:8000
    backend = 127.0.0.1:8080
    cache-size = 1G

This configures a buildout part which runs Varnish to listen on 127.0.0.1:8000
for requests, using a 1 gigabyte cache and sending requests to a backend 
at 127.0.0.1:8080 .

Options
-------

url
    URL for an archive containing the Varnish sources. Either **url** or
    **svn** has to be specified.

svn
    URL for a subversion repository containing Varnish sources. Either **url**
    or **svn** has to be specified.

cache-size
    The size of the cache.

bind
    Hostname, and optionally port, on which Varnish should listen for requests.
    Defaults to 127.0.0.1:8000.

backend
    Hostname, and optionally port, for the backend server. Defaults to
    127.0.0.1:8080.

telnet
    If specified sets the hostname and port on which Varnish will listen
    for commands using its telnet interface.


.. _Varnish: http://varnish.projects.linpro.no/
.. _zc.buildout: http://cheeseshop.python.org/pypi/zc.buildout
