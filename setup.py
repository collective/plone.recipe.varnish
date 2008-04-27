from setuptools import setup, find_packages

version = '1.0rc6'

setup(name='plone.recipe.varnish',
      version=version,
      description="Buildout recipe to install varnish",
      long_description=open("README.txt").read() + "\n" + \
                       open("CHANGES.txt").read(),
      classifiers=[
        "Framework :: Buildout",
        "Framework :: Zope2",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX",
        "Topic :: Internet :: Proxy Servers",
        ],
      keywords='buildout varnish cache proxy',
      author='Wichert Akkerman',
      author_email='wichert@wiggy.net',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
      ],
      entry_points={
          "zc.buildout" : [
              "build = plone.recipe.varnish:BuildRecipe",
              "instance = plone.recipe.varnish:ConfigureRecipe",
              ],
      }
      )
