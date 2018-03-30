=====================
Varnish VCL Generator
=====================

Prepare::

    >>> from plone.recipe.varnish.vclgen import VclGenerator

Initialization checks
=====================

Check init fails on wrong version::

    >>> config = {
    ...     'version': '3'
    ... }
    >>> VclGenerator(config)
    Traceback (most recent call last):
    ...
    UserError: Varnish version must be one out of ['6', '5', '4']. Got: 3. Use an older version of this recipe to support older Varnish. Newer versions than listed here are not supported.

Correct versions::

    >>> config = {
    ...     'version': '4'
    ... }
    >>> VclGenerator(config)
    <plone.recipe.varnish.vclgen.VclGenerator object at 0x...>

with Varnish 5::

    >>> config = {
    ...     'version': '5'
    ... }
    >>> VclGenerator(config)
    <plone.recipe.varnish.vclgen.VclGenerator object at 0x...>

And with Varnish 6::

    >>> config = {
    ...     'version': '6'
    ... }
    >>> VclGenerator(config)
    <plone.recipe.varnish.vclgen.VclGenerator object at 0x...>


Check single functionalities
============================

Directors
---------

Type must match::

    >>> config['directors'] = [
    ...     {'type': 'unknown', 'name': 'sellerie'}
    ... ]
    >>> vg = VclGenerator(config)
    >>> vg._directors()
    Traceback (most recent call last):
    ...
    UserError: director type unknown not supported.

Type must match::

    >>> config['directors'] = [
    ...     {'type': 'round_robin', 'name': 'sellerie'}
    ... ]
    >>> config['directors'][0]['backends'] = [
    ... ]
    >>> vg = VclGenerator(config)
    >>> pprint(vg._directors())
    [{'backends': [], 'name': 'sellerie', 'type': 'round_robin'}]


Add some backends::

    >>> config['directors'][0]['backends'] = [
    ...     'backend_001',
    ...     'backend_002',
    ... ]
    >>> vg = VclGenerator(config)
    >>> pprint(vg._directors())
    [{'backends': ['backend_001', 'backend_002'],
      'name': 'sellerie',
      'type': 'round_robin'}]

VHostings
---------

Basic check::

    >>> config = {
    ...     'version': '5',
    ...     'backends': [],
    ...     'zope2_vhm_map': {},
    ...     'custom': '',
    ...     'cookiewhitelist': ['statusmessages', '__ac',],
    ...     'cookiepass': [
    ...         {'match': '__ac(|_(name|password|persistent))=',
    ...          'exclude': '\.(js|css|kss)' }
    ...     ],
    ...     'gracehealthy': '10s',
    ...     'gracesick': '1h',
    ...     'code404page' : True,
    ... }
    >>> vg = VclGenerator(config)
    >>> vg._vhostings([])
    []

Add one backend as *2-tuple* (w/o url), the one host scenario::

    >>> config['backends'] = [
    ...     {
    ...         'name': 'backend_000',
    ...         'url': None,
    ...         'host': '10.11.22.33',
    ...         'port': '8080',
    ...         'connect_timeout': '10',
    ...         'first_byte_timeout': '20',
    ...         'between_bytes_timeout': '30',
    ...     }
    ... ]
    >>> vg = VclGenerator(config)
    >>> pprint(vg._vhostings([]))
    [{'setters': OrderedDict([('req.backend_hint', 'backend_000')])}]


Two backends, one with host match, other one with url match, third with both,
also ::

    >>> config['backends'] = [
    ...     {
    ...         'name': 'backend_000',
    ...         'url': 'plone.org',
    ...         'host': '10.11.22.33',
    ...         'port': '8080',
    ...     },
    ...     {
    ...         'name': 'backend_001',
    ...         'url': '/Plone/',
    ...         'host': '10.12.34.56',
    ...         'port': '8081',
    ...     },
    ...     {
    ...         'name': 'backend_002',
    ...         'url': 'zope.org:/foo/bar',
    ...         'host': '10.23.45.67',
    ...         'port': '8082',
    ...     },
    ... ]
    >>> config['zope2_vhm_map'] = {
    ...     'plone.org': {'location': '/PloneOrg', 'proto': 'http', 'external_port': '80'}
    ... }
    >>> vg = VclGenerator(config)
    >>> pprint(vg._vhostings([]))
    [{'match': 'req.http.host ~ "^plone.org(:[0-9]+)?$"',
      'setters': OrderedDict([('req.backend_hint', 'backend_000'), ('req.url', '"/VirtualHostBase/http/plone.org:80/PloneOrg/VirtualHostRoot" + req.url')])},
     {'match': 'req.url ~ "^/Plone/"',
      'setters': OrderedDict([('req.backend_hint', 'backend_001')])},
     {'match': 'req.http.host ~ "^[zope.org](:[0-9]+)?$" && req.url ~ "^/foo/bar"',
      'setters': OrderedDict([('req.backend_hint', 'backend_002')])}]


Combine Backends and directors::

    >>> config['backends'] = [
    ...     {
    ...         'name': 'backend_000',
    ...         'url': 'plone.org',
    ...         'host': '10.11.22.33',
    ...         'port': '8080',
    ...         'connect_timeout': '0.41s',
    ...         'first_byte_timeout': '299s',
    ...         'between_bytes_timeout': '59s',
    ...     },
    ...     {
    ...         'name': 'backend_001',
    ...         'url': 'plone.org',
    ...         'host': '10.11.22.34',
    ...         'port': '8080',
    ...         'connect_timeout': '0.42s',
    ...         'first_byte_timeout': '298s',
    ...         'between_bytes_timeout': '58s',
    ...     },
    ...     {
    ...         'name': 'backend_010',
    ...         'url': 'python.org',
    ...         'host': '10.11.22.35',
    ...         'port': '8080',
    ...         'connect_timeout': '0.43s',
    ...         'first_byte_timeout': '297s',
    ...         'between_bytes_timeout': '57s',
    ...     },
    ...     {
    ...         'name': 'backend_011',
    ...         'url': 'python.org',
    ...         'host': '10.11.22.36',
    ...         'port': '8080',
    ...         'connect_timeout': '0.44s',
    ...         'first_byte_timeout': '296s',
    ...         'between_bytes_timeout': '56s',
    ...     },
    ...     {
    ...         'name': 'backend_020',
    ...         'url': 'single.org',
    ...         'host': '10.11.22.37',
    ...         'port': '8080',
    ...         'connect_timeout': '0.45',
    ...         'first_byte_timeout': '295s',
    ...         'between_bytes_timeout': '55s',
    ...     },
    ... ]
    >>> config['zope2_vhm_map'] = {
    ...     'plone.org': {'location': '/PloneOrg', 'proto': 'http', 'external_port': '80'}
    ... }
    >>> config['directors'] = [
    ...     {
    ...         'type': 'round_robin',
    ...         'name': 'alpha',
    ...         'backends': ['backend_000', 'backend_001']
    ...     },
    ...     {
    ...         'type': 'random',
    ...         'name': 'beta',
    ...         'backends': ['backend_010', 'backend_011']
    ...     },
    ... ]
    >>> vg = VclGenerator(config)
    >>> directors = vg._directors()
    >>> pprint(directors)
    [{'backends': ['backend_000', 'backend_001'],
      'name': 'alpha',
      'type': 'round_robin'},
     {'backends': ['backend_010', 'backend_011'],
      'name': 'beta',
      'type': 'random'}]

    >>> pprint(vg._vhostings(directors))
    [{'match': 'req.http.host ~ "^plone.org(:[0-9]+)?$"',
      'setters': OrderedDict([('req.backend_hint', 'alpha.backend()'), ('req.url', '"/VirtualHostBase/http/plone.org:80/PloneOrg/VirtualHostRoot" + req.url')])},
     {'match': 'req.http.host ~ "^python.org(:[0-9]+)?$"',
      'setters': OrderedDict([('req.backend_hint', 'beta.backend()')])},
     {'match': 'req.http.host ~ "^single.org(:[0-9]+)?$"',
      'setters': OrderedDict([('req.backend_hint', 'backend_020')])}]

Check purgehosts. add some manual and then all above hosts should be in too::

    >>> config['purgehosts'] = ['192.168.1.2', '123.123.123.123',]
    >>> vg = VclGenerator(config)
    >>> pprint(vg._purgehosts())
    set(['10.11.22.33',
         '10.11.22.34',
         '10.11.22.35',
         '10.11.22.36',
         '10.11.22.37',
         '123.123.123.123',
         '192.168.1.2'])

Unix domain sockets as backend addresses::

    >>> config['version'] = '6'
    >>> config['vcl_version'] = '4.1'
    >>> config['backends'] = [
    ...     {
    ...         'name': 'backend_030',
    ...         'url': 'foo.org',
    ...         'path': '/tmp/foo.sock',
    ...         'connect_timeout': '0.45',
    ...         'first_byte_timeout': '295s',
    ...         'between_bytes_timeout': '55s',
    ...     },
    ... ]

    >>> vg = VclGenerator(config)
    >>> pprint(vg._vhostings(directors))
    [{'match': 'req.http.host ~ "^foo.org(:[0-9]+)?$"',
      'setters': OrderedDict([('req.backend_hint', 'backend_030')])}]

Generate!

    >>> result = vg()
    >>> len(result) > 8000
    True
