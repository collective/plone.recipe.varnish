# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


version = '2.3.0'

setup(
    name='plone.recipe.varnish',
    version=version,
    description="Build and/or configure Varnish Cache with zc.buildout",
    long_description=(
        open("README.rst").read() + "\n" +
        open("CHANGES.rst").read()
    ),
    classifiers=[
        "Framework :: Buildout",
        "Framework :: Zope2",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: Proxy Servers",
    ],
    keywords='buildout varnish cache proxy',
    author='Wichert Akkerman, et al',
    author_email='wichert@wiggy.net',
    url='https://pypi.python.org/pypi/plone.recipe.varnish',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['plone', 'plone.recipe'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'jinja2>=2.7.3',
        'setuptools',
        'zc.buildout',
        'zc.recipe.cmmi',
    ],
    extras_require = dict(
        test=['interlude', 'ipdb']
    ),
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
    entry_points={
        "zc.buildout": [
            "build = plone.recipe.varnish.recipe:BuildRecipe",
            "configuration = plone.recipe.varnish.recipe:ConfigureRecipe",
            "script = plone.recipe.varnish.recipe:ScriptRecipe",
        ],
    },
)
