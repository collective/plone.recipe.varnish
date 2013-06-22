Changelog
=========

1.3 (unreleased)
----------------

- Add varnish_version option in order to control vcl generation for
  varnish version >= 3
  [rnix]


1.2.2 (2012-10-14)
------------------

- Moved to https://github.com/collective/plone.recipe.varnish
  [maurits]


1.2.1 (2011-05-13)
------------------

- Update known good Varnish to 2.1.5.
  [elro]

- Add vcl_recv, vcl_hit, vcl_miss, vcl_fetch, vcl_deliver, vcl_pipe options to
  insert arbitrary vcl.
  [elro]


1.2 (2011-01-11)
----------------

- Added new options ``cache-type``, ``cache-location`` for specifying type of
  Varnish storage (such as using malloc for alternative storage) and setting a
  custom location for said storage
  [davidjb]

- Added additional unit tests to check Varnish initialisation script
  [davidjb]

- Added new option 'purge-hosts'. Enables additional addresses allowed to purge.
  [jensens]

- Added the `name` option to be able to define the directory varnishd
  puts temporary files to and identify the instance when using varnishlog
  or varnishstat.
  [fRiSi]

- fixed configuration for verbose-headers=on (context in vlc_fetch is
  bresp instead of obj in newer varnish versions)
  [fRiSi]

1.1 (2010-08-05)
----------------

- Changed the default cache size to 256M from 1G.
  [hannosch]

- Updated Varnish to 2.1.3.
  [hannosch]

1.1b1 (2010-04-25)
------------------

- Updated advertised Varnish version to 2.1 and adjusted config.
  [hannosch]

- Correct documentation for the ``daemon`` setting and remove the default.
  [hannosch]

- Removed the deprecated build recipe.
  [hannosch]

- Added basic test infrastructure and a test for the simple buildout.
  [hannosch]

- Use the built-in set type instead of the deprecated sets module. This recipe
  now requires at least Python 2.4.
  [hannosch]

- Added the ability to configure runtime parameters in the varnish runner
  configuration and added information to the documentation for it.
  [benliles]

- Improve readability of the generated config.
  [ldr]

1.0.2 (2010-01-18)
------------------

- Update proposed Varnish to 2.0.6.
  [hannosch]

- Further documentation cleanup.
  [hannosch, vincentfretin]

1.0.1 (2009-11-27)
------------------

- Expose the ``download-url`` of a known-good Varnish release that works with
  the configuration produced by the instance recipe.
  [hannosch]

- Consistently use tabs in the generated vcl file.
  [hannosch]

- Whitespace and documentation cleanup.
  [hannosch]


1.0 (2009-08-27)
----------------

* Made the vcl template build its acl purge section. At present, the vcl will
  only allow purges coming from the local host. If we have multiple hosts that
  are separate from localhost, any PURGE requests will be denied without this.
  See http://varnish.projects.linpro.no/wiki/VCLExamplePurging
  [rockdj]

* Added ability to set various Varnish timeouts (connect_timeout,
  first_byte_timeout, and between_bytes_timeout) from each option in the
  buildout. Default values are set at Varnish defaults of 0.4s for
  connect_timeout, and 60s for between_bytes_timeout. Time for
  first_byte_timeout is set at 300s as per plone.recipe.varnish 1.0rc9.
  [rockdj]

* Set `req.http.host` for incoming virtual hosted URLs. Without setting this,
  purge requests sent from hosts other than localhost (the only host in the acl
  purge list) will result in a 404 message. See
  http://davidjb.com/blog/2009/01/plone-varnish-configuration-cache-hits-purge-fails
  [rockdj]


1.0rc11 (2009-06-27)
--------------------

* Reintroduced grace options. What the varnish documentation say about grace:
  "varnish serves stale (but cacheable) objects while retrieving object from
  backend". The problem is "default_ttl" value is 120s (see
  bin/varnishd/mgt_param.c in varnish 2.0.4). Added a special rule for
  createObject url to not look up in the cache.
  [vincentfretin]


1.0rc10 (2009-06-26)
--------------------

* 1.0rc9 generated broken configuration with balancer=none
  [vincentfretin]


1.0rc9 (2009-06-25)
-------------------

* Do not set req.grace and obj.grace. See
  http://vincentfretin.ecreall.com/articles/varnish-user-be-careful
  [vincentfretin, maurits]

* Removed `header_hit_deliver` and `header_hit_notcacheable` debug messages
  from default template. It is not safe to assign to the object during
  `vcl_hit` until http://varnish.projects.linpro.no/ticket/310 is not fixed.
  See also http://kristian.blog.linpro.no/2009/05/25/common-varnish-issues.
  [hannosch]

* Updated to refer to Varnish 2.0.4. Added a `first_byte_timeout` value of
  300 seconds to the backend definitions. This is a new option since Varnish
  2.0.3 and by default set to 60 seconds. This is arguably too low for certain
  edit operations in Plone sites.
  [hannosch]


1.0rc8 (2008-02-12)
-------------------

* Remove the custom vcl_hash from the template. Adding the Accept-Encoding
  header to the cache break effectively breaks purging since nobody will
  ever include those headers in a PURGE request. To make this safe we just
  remove the Accept-Encoding header from all incoming requests as well.
  [wichert]


1.0rc7 (2008-11-26)
-------------------

* Be more explicit about deprecating the :build entry point.
  [wichert]

* Make the :instance specifier optional: after :build has been removed
  we can deprecate :instance as well.
  [wichert]


1.0rc6 (2008-09-22)
-------------------

* Deprecate plone.recipe.varnish:build in favour of zc.recipe.cmmi: it does
  not make sense to duplicate its logic here.
  [wichert]

* Add feature to enable verbose headers in varnish.vcl. This is primary
  interesting for debugging of cache-settings. See README.txt.
  [jensens]

* Deal better with sources which do not have executable-bits set or
  are svn exports.
  [wichert]

* The 1.0rc5 release was broken and has been retracted. Currently the trunk
  is only usable with the Varnish 2.0-beta1 and later.
  [hannosch]


1.0rc5 (2008-04-27)
-------------------

* Pipe is evil: it pipes the whole connection to the backend which means
  varnish will no longer process any further requests if HTTP pipelining is
  used. Switch to using pass instead.
  [wichert]

* Add a default_ttl of zero seconds to the Varnish runner to avoid a Varnish
  bug with the handling of an Expires header with a date in the past.
  [newbery]

* Merged branches/newbery-hostnamepath.
  [newbery]

* We don't need to include Accept-Encoding in the hash. Varnish takes care
  of Vary negotiation already.
  [newbery]


1.0rc4 (2008-03-18)
-------------------

* Fixed typos / whitespace.
  [hannosch]

* Varnish 1.1.2 is out.
  [wichert]

* Merged witsch-foreground-support back to trunk.
  [witsch]

* Use a pidfile.
  [wichert]


1.0rc3 (2007-09-02)
-------------------

* Fixed a bug where options["location"] was being used before it was being set.
  [rocky]

* Made the module name determination a little more robust during
  createVarnishConfig so that recipes that specify version deps still work.
  [rocky]

* Do not use defaults for user and group.
  [wichert]

* We do need the parts: we use it for the file storage.
  [wichert]


1.0rc2 (2007-08-29)
-------------------

* Add an option to use an existing configuration file.
  [wichert]

* Remove hardcoded caching for images, binaries, CSS and javascript. This
  should be done by the backend server or a custom varnish configuration.
  [wichert]

* Add Accept-Encoding to the cache key so we can handle compressed content.
  [wichert]

* Test if a bin-directory exists. This allows us to compile varnish 1.0
  which does not have an sbin directory.
  [wichert]


1.0rc1 (2007-08-27)
-------------------

* Document the OSX bugfix we apply when building varnish.
  [wichert]

* Add a dummy update method to prevent needless recompiles.
  [wichert]

* Update for Varnish 1.1.1.
  [wichert]


1.0b2 (2007-08-25)
------------------

* When building from svn, we need to run autogen.sh.
  [optilude]

* Refactor the recipe: there are now separate recipes to build and configure
  Varnish. This makes it possible to reconfigure varnish without having to
  recompile with as well as using an already installed varnish.
  [wichert]

* Move the OSX patching code into a separate method.
  [wichert]

* Use pass for non-GET/HEAD requests. This makes a bit more sense and fixes a
  login problem for Plone sites.
  [wichert]

* Reorganize a bit for readability.
  [wichert]

* Support Python 2.3 as well.
  [wichert]

* Make it possible to specify the user and group as well.
  [wichert]

* Do not create the source directory - we move the extracted source in its
  place later.
  [wichert]

* If running on OS X, patch libtool as described in
  http://varnish.projects.linpro.no/ticket/118 and
  http://thread.gmane.org/gmane.comp.web.varnish.misc/668/focus=669.
  [optilude]

* VCL is not C. You need the curlies even on single-line if statements.
  [optilude]

* This rewriting style only works on Zope 3 - Zope 3 reinvented that wheel.
  [wichert]

* Add support for If-Modified-Since and If-None-Match requests.
  Thanks to newbery for the suggstions.
  [wichert]

* Explicitly mention that there is nothing Plone or Zope specific about
  this recipe.
  [wichert]


1.0b1 (2007-08-04)
------------------

* More documentation.
  [wichert]

* Ignore the port information in the host header.
  [wichert]

* Use the port varnish is bound to in the VHM mapping.
  [wichert]

* Define all default values centrally.
  [wichert]

* Add support for Zope virtual hosts.
  [wichert]

* Add support for virtual hosting.
  [wichert]

* Initial import of Varnish recipe.
  [wichert]
