# -*- coding: utf-8 -*-
from interlude import interact
from zc.buildout.testing import buildoutSetUp
from zc.buildout.testing import buildoutTearDown
from zc.buildout.testing import install
from zc.buildout.testing import install_develop

import commands
import doctest
import shutil
import unittest


FLAGS = \
    doctest.ELLIPSIS | \
    doctest.NORMALIZE_WHITESPACE | \
    doctest.REPORT_ONLY_FIRST_FAILURE
# We used to have a custom exec_system from zc.buildout,
# but that one fails to give output back with varnish 4.1.
# So we fall back to a simpler version.
exec_system = commands.getoutput


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
