from setuptools import setup, find_packages

version = '1.1b1'

setup(name='plone.recipe.varnish',
      version=version,
      description="Buildout recipe to install varnish",
      long_description=open("README.txt").read() + "\n" + \
                       open("CHANGES.txt").read(),
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
      url='http://pypi.python.org/pypi/plone.recipe.varnish',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zc.buildout',
      ],
      extras_require = dict(test=['zc.recipe.cmmi']),
      entry_points={
          "zc.buildout": [
              "default = plone.recipe.varnish:ConfigureRecipe",
              "instance = plone.recipe.varnish:ConfigureRecipe",
              ],
      },
      )
