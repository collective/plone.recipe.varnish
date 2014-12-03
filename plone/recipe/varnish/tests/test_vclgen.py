# -*- coding: utf-8 -*-
from interlude import interact
from pprint import pprint
import doctest
import unittest

FLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    suite = [
        doctest.DocFileSuite(
            'vclgen.rst',
            optionflags=FLAGS,
            globs={'interact': interact, 'pprint': pprint},
        ),
    ]
    return unittest.TestSuite(suite)

if __name__ == '__main__':
    unittest.main()
