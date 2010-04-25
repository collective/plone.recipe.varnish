# -*- coding: utf-8 -*-

import doctest
import unittest
import shutil

from zc.buildout.testing import buildoutSetUp
from zc.buildout.testing import buildoutTearDown
from zc.buildout.testing import install
from zc.buildout.testing import install_develop


def setUp(test):
    buildoutSetUp(test)
    install_develop('plone.recipe.varnish', test)
    install('zc.recipe.cmmi', test)


def tearDown(test):
    buildoutTearDown(test)
    sample_buildout = test.globs['sample_buildout']
    shutil.rmtree(sample_buildout, ignore_errors=True)


def test_suite():
    suite = []
    flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

    suite.append(doctest.DocFileSuite('varnish.txt', optionflags=flags,
                 setUp=setUp, tearDown=buildoutTearDown))

    return unittest.TestSuite(suite)
