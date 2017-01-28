# -*- coding: utf-8 -*-
from interlude import interact
from zc.buildout.testing import buildoutSetUp
from zc.buildout.testing import buildoutTearDown
from zc.buildout.testing import install
from zc.buildout.testing import install_develop

import doctest
import shutil
import subprocess
import sys
import unittest


FLAGS = \
    doctest.ELLIPSIS | \
    doctest.NORMALIZE_WHITESPACE | \
    doctest.REPORT_ONLY_FIRST_FAILURE

# FIXME - check for other platforms
MUST_CLOSE_FDS = not sys.platform.startswith('win')


def exec_system(command, input='', with_exit_code=False):
    p = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=MUST_CLOSE_FDS
    )
    i, o, e = (p.stdin, p.stdout, p.stderr)
    if input:
        i.write(input.encode('utf8'))
    i.close()
    result = o.read() + e.read()
    o.close()
    e.close()
    output = result.decode('utf-8')
    if with_exit_code:
        # Use the with_exit_code=True parameter when you want to test the exit
        # code of the command you're running.
        output += 'EXIT CODE: %s' % p.wait()
    return output


def setUp(test):
    buildoutSetUp(test)
    install('zc.recipe.cmmi', test)
    install('jinja2', test)
    install('markupsafe', test)
    install_develop('plone.recipe.varnish', test)


def tearDown(test):

    buildoutTearDown(test)
    sample_buildout = test.globs['sample_buildout']
    shutil.rmtree(sample_buildout, ignore_errors=True)


def test_suite():
    suite = [
        doctest.DocFileSuite(
            'recipe.rst',
            optionflags=FLAGS,
            setUp=setUp,
            tearDown=tearDown,
            globs={'interact': interact, 'exec_system': exec_system},
        )
    ]

    return unittest.TestSuite(suite)


if __name__ == '__main__':
    unittest.main()
