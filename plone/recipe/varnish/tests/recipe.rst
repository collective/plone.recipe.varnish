Varnish recipe
==============

This is the doctest for plone.recipe.varnish. It ensures the template
works fine. It is based on zc.buildout testing module::

    >>> from zc.buildout.testing import write
    >>> import os
    >>> import sys

    >>> buildout_bin = os.path.join('bin', 'buildout')
    >>> varnish_bin = os.path.join('bin', 'varnish')
    >>> system = exec_system

Let's create a minimum buildout that uses the current plone.recipe.varnish::

    >>> simplest = '''
    ... [buildout]
    ... parts = varnish-build varnish-configuration varnish
    ... find-links = %(sample_buildout)s/eggs
    ...
    ... [varnish-build]
    ... recipe = plone.recipe.varnish:build
    ... jobs = 4
    ...
    ... [varnish-configuration]
    ... recipe = plone.recipe.varnish:configuration
    ... daemon = ${varnish-build:location}/sbin/varnishd
    ... backends = 127.0.0.1:8081
    ...
    ... [varnish]
    ... recipe = plone.recipe.varnish:script'''
    >>> write('buildout.cfg', simplest % globals())

Let's run it::

    >>> print system(buildout_bin)
    Installing varnish-build.
    varnish-build: Downloading ...
    varnish-build: Unpacking and configuring
    ...

A control script got created::

    >>> 'varnish' in os.listdir('bin')
    True

Check the contents of the control script are correct::

    >>> print open(varnish_bin).read()
    #!/bin/sh
    exec ...sample-buildout/parts/varnish-build/sbin/varnishd \
        -f "...sample-buildout/parts/varnish-configuration/varnish.vcl" \
        -P "...sample-buildout/parts/varnish/varnish.pid" \
        -a 127.0.0.1:8000 \
        -s file,"...sample-buildout/parts/varnish/storage",256M \
        "$@"
    <BLANKLINE>

Check the config is syntactically correct by compiling it to C::

    >>> print system(varnish_bin + ' -C')
    /* ---===### include/vcl.h ###===--- */
    <BLANKLINE>
    /*
     * NB:  This file is machine generated, DO NOT EDIT!
     *
     * Edit and run generate.py instead
     */
    <BLANKLINE>
    ...
    const struct VCL_conf VCL_conf = {
    ...

Test out customising the storage options with a new test buildout::

    >>> file_storage = '''
    ... cache-type = file
    ... cache-location = %(sample_buildout)s/custom_storage
    ... cache-size = 3.14G
    ... '''
    >>> write('buildout.cfg', (simplest+file_storage) % globals())

Let's run it::

    >>> print system(buildout_bin)
    Uninstalling varnish.
    Updating varnish-build.
    Updating varnish-configuration.
    Installing varnish.
    ...

Check the contents of the control script are correct::

    >>> 'varnish' in os.listdir('bin')
    True

    >>> print open(varnish_bin).read()
    #!/bin/sh
    ...
        -s file,"...sample-buildout/custom_storage",3.14G \
    ...

Customising our storage options again to check we can work with malloc as
well::

    >>> mem_storage = simplest + '''
    ... cache-type = malloc
    ... cache-size = 2.71G
    ... '''
    >>> write('buildout.cfg', mem_storage % globals())

Let's run it::

    >>> print system(buildout_bin)
    Uninstalling varnish.
    Updating varnish-build.
    Updating varnish-configuration.
    Installing varnish.
    ...
    
Check the contents of the control script reflect our new options::

    >>> 'varnish' in os.listdir('bin')
    True

    >>> print open(varnish_bin).read()
    #!/bin/sh
    ...
        -s malloc,2.71G \
    ...

Test the varnish download with an older version::

    >>> varnish_4 = simplest + '''
    ... varnish_version = 4
    ... download-url = https://repo.varnish-cache.org/source/varnish-4.0.2.tar.gz
    ... '''
    >>> write('buildout.cfg', varnish_4 % globals())

Let's run it::

    >>> print system(buildout_bin)
    Uninstalling varnish.
    Updating varnish-build.
    Updating varnish-configuration.
    Installing varnish.
    ...