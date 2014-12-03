=====================
Varnish VCL Generator
=====================

Prepare::

    >>> from plone.recipe.varnish.vclgen import VclGenerator

Initialization checks
=====================

Check init fails on wrong version::

    >>> config = {
    ...     'major_version': 3
    ... }
    >>> VclGenerator(config)
    Traceback (most recent call last):
    ...
    UserError: Varnish version must be one of [4]. Use an older version of
    this recipe to support older Varnish. Newer versions than listed here are
    not supported.

Correct version::

    >>> config = {
    ...     'major_version': 4
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
    ...     {'type': 'round-robin', 'name': 'sellerie'}
    ... ]
    >>> config['directors'][0]['backends'] = [
    ... ]
    >>> vg = VclGenerator(config)
    >>> pprint(vg._directors())
    [{'backends': [], 'name': 'sellerie', 'type': 'round-robin'}]


Add some backends::

    >>> config['directors'][0]['backends'] = [
    ...     'backend_1',
    ...     'backend_2',
    ... ]
    >>> vg = VclGenerator(config)
    >>> pprint(vg._directors())
    [{'backends': ['backend_1', 'backend_2'],
      'name': 'sellerie',
      'type': 'round-robin'}]

    >>> interact(locals())


