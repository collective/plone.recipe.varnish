from setuptools import setup, find_packages

version = '1.0b1'

setup(name='plone.recipe.varnish',
      version=version,
      description="Buildout recipe to install varnish",
      long_description=open("README.txt").read(),
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        ],
      keywords='buildout varnish cache proxy',
      author='Wichert Akkerman',
      author_email='wichert@wiggy.net',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points={
          "zc.buildout" : [ "default = plone.recipe.varnish:Recipe" ],
      }
      )

