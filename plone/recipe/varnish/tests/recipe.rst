Varnish recipe
==============

This is the doctest for plone.recipe.varnish. It ensures the template
works fine. It is based on zc.buildout testing module::

    >>> from zc.buildout.testing import write
    >>> import os
    >>> import sys

    >>> buildout_bin = os.path.join('bin', 'buildout')
    >>> varnish_bin = os.path.join('bin', 'varnish')
    >>> varnishd = os.path.join('parts/varnish-build/sbin', 'varnishd')
    >>> system = exec_system

Let's create a minimum buildout that uses the current plone.recipe.varnish::

    >>> simplest = '''
    ... [buildout]
    ... parts = varnish-build varnish-configuration varnish
    ... find-links = %(sample_buildout)s/eggs
    ... index = https://pypi.org/simple/
    ... [varnish-build]
    ... recipe = plone.recipe.varnish:build
    ... compile-vmods = true
    ... jobs = 4
    ...
    ... [varnish-configuration]
    ... recipe = plone.recipe.varnish:configuration
    ... daemon = ${varnish-build:location}/sbin/varnishd
    ... backends = 127.0.0.1:8081
    ... vcl_import = import header; import xkey;
    ...
    ... [varnish]
    ... recipe = plone.recipe.varnish:script'''
    >>> write('buildout.cfg', simplest % globals())

Let's run it::

    >>> output = system(buildout_bin)
    >>> if 'Traceback' in output:
    ...     print(output)
    >>> if 'Installing varnish-build.' not in output:
    ...     print(output)
    >>> if 'varnish-build: Downloading' not in output:
    ...     print(output)
    >>> if 'varnish-build: Unpacking and configuring' not in output:
    ...     print(output)

A control script got created::

    >>> 'varnish' in os.listdir('bin')
    True

Check the contents of the control script are correct::

    >>> print(open(varnish_bin).read())
    #!/bin/sh
    exec ...sample-buildout/parts/varnish-build/sbin/varnishd \
        -f "...sample-buildout/parts/varnish-configuration/varnish.vcl" \
        -P "...sample-buildout/parts/varnish/varnish.pid" \
        -a 127.0.0.1:8000 \
        -s file,"...sample-buildout/parts/varnish/storage",256M \
        "$@"
    <BLANKLINE>

Check the config with Varnish is syntactically correct by compiling it to C::
    >>> print(system(varnish_bin + ' -C'))
    /* VCC_INFO VMOD...
    /* ---===### include/vdef.h ###===--- */
    <BLANKLINE>
    ...
    /* --- BEGIN VMOD header --- */
    ...
    /* --- BEGIN VMOD xkey --- */
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

    >>> output = system(buildout_bin)
    >>> if 'Traceback' in output:
    ...     print(output)
    >>> if 'Uninstalling varnish.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-build.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-configuration.' not in output:
    ...     print(output)
    >>> if 'Installing varnish.' not in output:
    ...     print(output)

Check the contents of the control script are correct::

    >>> 'varnish' in os.listdir('bin')
    True

    >>> print(open(varnish_bin).read())
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

    >>> output = system(buildout_bin)
    >>> if 'Traceback' in output:
    ...     print(output)
    >>> if 'Uninstalling varnish.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-build.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-configuration.' not in output:
    ...     print(output)
    >>> if 'Installing varnish.' not in output:
    ...     print(output)

Check the contents of the control script reflect our new options::

    >>> 'varnish' in os.listdir('bin')
    True

    >>> print(open(varnish_bin).read())
    #!/bin/sh
    ...
        -s malloc,2.71G \
    ...

Check if we can disable the pre shared key secret file for varnishadm access::

    >>> disable_secret = simplest + '''
    ... secret-file = disabled
    ... '''
    >>> write('buildout.cfg', disable_secret % globals())

Let's run it::

    >>> output = system(buildout_bin)
    >>> if 'Traceback' in output:
    ...     print(output)
    >>> if 'Uninstalling varnish.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-build.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-configuration.' not in output:
    ...     print(output)
    >>> if 'Installing varnish.' not in output:
    ...     print(output)

Check the contents of the control script reflect our new options::

    >>> 'varnish' in os.listdir('bin')
    True

    >>> print(open(varnish_bin).read())
    #!/bin/sh
    ...
        -S "" \
    ...

Check if we can specify a key file for varnishadm access::

    >>> enable_secret = simplest + '''
    ... secret-file = ${buildout:directory}/var/varnish-secret
    ... '''
    >>> write('buildout.cfg', enable_secret % globals())

Let's run it::

    >>> output = system(buildout_bin)
    >>> if 'Traceback' in output:
    ...     print(output)
    >>> if 'Uninstalling varnish.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-build.' not in output:
    ...     print(output)
    >>> if 'Updating varnish-configuration.' not in output:
    ...     print(output)
    >>> if 'Installing varnish.' not in output:
    ...     print(output)

Check the contents of the control script reflect our new options::

    >>> 'varnish' in os.listdir('bin')
    True

    >>> print(open(varnish_bin).read())
    #!/bin/sh
    ...
        -S .../sample-buildout/var/varnish-secret \
    ...

Check if Varnish default version is 6.0.x::

    >>> output = system(varnishd + ' -V')
    >>> if 'varnishd (varnish-6.0.' not in output:
    ...     print(output)
