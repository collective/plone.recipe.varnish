Todo
====

Area's this recipe could further be improved. 

* Explore the use of varnishtest. Varnishtest is the testing framework Varnish
  uses internally to validate cache functionalite. I have seen regressions in for
  example purging functionality because of minor Varnish updates or small tweaks
  in Plone. We are already building Varnish in the receipe test setup, so we
  could prevent these from happening unnoticed by adding a few varnishtest
  scenario's. See
  https://github.com/varnishcache/varnish-cache/tree/master/bin/varnishtest/tests

* Improve purging. There are more clever purging schemes possible than the
  current purge setup. One possible setup is by using secondary cache key
  functionality as is done by https://pypi.org/project/collective.purgebyid/ .
  Another option is to start using

* The backends/redirector functions in the recipe and VCL generator are
  interdependent, complex and at the moment still miss the use case where you can
  have 4 backends for 2 sites. The backends should first be sorted on the
  domain/vhm/hostname part and then 2 directors should be created with each 2
  backends.

* Sticky sessions support in the directores when Varnish does load balancing
  to the backends. There is some discussion in the github issues for the recipe repo.
  Also see this blog post on the Varnish Software website:
  https://info.varnish-software.com/blog/proper-sticky-session-load-balancing-varnish

* Enable compilation/adding varnish modules (VMOD's). This is really painfull.
  There a a few really usefull vmods that can simplify required vcl for cookie
  sanitizing, header manipulation etc. https://github.com/varnish/varnish-modules
  contains a repo of several of these modules. I have looked and tries this, but
  to compile extra vmods you first need to build varnish itself from source and
  vmod distributions require access to several M4 macro files from the Extracted
  Varnish source distribution. So you need a 2 phase build step and 'nested' CMMI
  so that the modules compilation can refer to the still extracted source files.
  IMHO launching Varnish as a container from an already prepped image with all
  modules built in or reusing binary packages from Linux distributions is the
  future of distributing these kind of software packages.
