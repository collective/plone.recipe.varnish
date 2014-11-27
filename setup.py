import os, sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


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


version = '1.4'

setup(name='plone.recipe.varnish',
      version=version,
      description="Buildout recipe to install varnish",
      long_description=(open("README.rst").read() + "\n" +
                        open("CHANGES.rst").read()),
      classifiers=[
          "Framework :: Buildout",
          "Framework :: Zope2",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: BSD License",
          "Operating System :: POSIX",
          "Topic :: Internet :: Proxy Servers",
          ],
      keywords='buildout varnish cache proxy',
      author='Wichert Akkerman',
      author_email='wichert@wiggy.net',
      url='https://pypi.python.org/pypi/plone.recipe.varnish',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zc.buildout',
      ],
      extras_require = dict(test=['zc.recipe.cmmi', 'interlude']),
      tests_require=['pytest'],
      cmdclass = {'test': PyTest},
      entry_points={
          "zc.buildout": [
              "default = plone.recipe.varnish:ConfigureRecipe",
              "instance = plone.recipe.varnish:ConfigureRecipe",
              ],
      },
      )
