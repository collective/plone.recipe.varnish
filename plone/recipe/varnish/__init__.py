# -*- coding: utf-8 -*-
from jinja2 import Environment
from jinja2 import PackageLoader


jinja2env = Environment(
    loader=PackageLoader('plone.recipe.varnish', 'templates'),
    trim_blocks=True,
    lstrip_blocks=True,
)
