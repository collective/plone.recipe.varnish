Changelog
=========

6.0.0b4 (2021-12-08)
--------------------

- Use Varnish 6.0.9 LTS.  [fredvd]

- Build VMODS [mamico]


6.0.0b3 (2020-07-15)
--------------------

- BUGFIX: omitting health-probe-url resulted in `.url = "None";` [frisi]


6.0.0b2 (2020-07-14)
--------------------

- Add options to configure backend health checks [frisi]

- Update documentation for health probes. [frisi]


6.0.0b1 (2020-02-26)
--------------------

- BREAKING: only support Varnish version 6.0 LTS and generates config (VCL) for this version
  only as well. If you want to use a different Varnish version with this recipe to use the
  software build and runner setup, provide your own VCL and a custom link to a Varnish
  download url. (Closes #70)
  [fredvd]

- Update to Varnish 6.0.6 LTS security release. [fredvd]

- Set default vcl_hash value so the fallback default.vcl hash function doesn't get activated. This
  will break purging because the hash from the incoming request on your public dns/hostname will
  never match the internal hostname when Plone makes the purge request. (Closes #61, Refs #70)

- Add an option to modify the health-check url defaulting to Plone's /ok view.
  [erral]

- Disable building sphinx documentation in the varnish-build/cmmi stage of installing the software.
  [fredvd]

- Update Varnish versions. Anything below 6.0.X is officially unmaintained. Update versions 6 and 6.0 to latest version 6.0.4
  [fredvd]

- Set default version to version 6, downloading 6.0.4 if no url is provided.
  [fredvd]



2.3.0 (2019-03-26)
------------------

- Simplified test buildout setup by not using plone versions.
  See `issue #69 <https://github.com/collective/plone.recipe.varnish/issues/69>`_.  [maurits]

- Updated default varnish 4 version to latest 4.1.11.  [maurits]

- Pick up vcl_hash custom code insertion again from the buildout recipe values.
  It was defined in the varnish templates but never picked up.
  [fredvd]

- Initial Varnish 6 support.
  [cleberjsantos]

- Fix custom vcl code insertion for ``vcl_purge``
  [mamico]

- Fix grace-sick default.
  [mamico]

2.2.0 (2018-01-05)
------------------

- Initial Varnish 5 support.
  vcl-version parameter has been added to control
  `Varnish VCL Syntax format version <https://book.varnish-software.com/4.0/chapters/VCL_Basics.html#vcl-syntax>`_.
  [maurits, jensens, cleberjsantos]


2.1.0 (2017-12-18)
------------------

- Use 4.1 version by default (4.0 was default until now).  [maurits]


2.0 (2017-12-15)
----------------

- When using varnish 4.1, use varnish 4.1.9.
  4.0 is still the default.  [cleberjsantos, maurits]

- fix default value for ``COOKIE_PASS_DEFAULT`` not matching any other
  urls than the intended static resources.
  [petschki]


2.0a8 (2017-11-03)
------------------

- New: refactor start script as Jinja2 template
  [petschki]

- Fix to failing travis tests, ``bin/createcoverage`` tries to open browser.
  [instification]

- Stripped query string before testing which urls to strip cookies on.
  https://github.com/collective/plone.recipe.varnish/issues/42 [instification]

- Fix custom vcl code insertion for ``vcl_backend_fetch`` and ``vcl_backend_response``
  Update documentation
  [petschki]

- Fix parameter for jailed user in ``varnish_version=4.1``
  [petschki]

- update documentation for ``varnish_version`` which only makes sense to be set in
  the build-part.
  [petschki]


2.0a7 (2017-08-16)
------------------

- Changed default downloads to ``.tgz`` instead of ``.tar.gz``.
  For some reason they were renamed after the last release of this recipe.
  [maurits]


2.0a6 (2017-08-15)
------------------

- Updated default urls to `varnish security releases <https://varnish-cache.org/security/VSV00001.html>`_.
  Also updated these urls to not use the ``repo.varnish-cache.org`` domain,
  because those links will stop working at `31 August 2017 <https://varnish-cache.org/news/index.html#package-repository-status>`_.
  [maurits]

- Fix VCL director: from round-robin to round_robin, tests refactored.
  [cleberjsantos]


2.0a5 (2016-08-29)
------------------

- Made three possible values for the ``varnish_version`` option.  4.0
  (uses 4.0.3), 4.1 (uses 4.1.3), 4 (uses 4.1.3).  4.0 is the default for now.
  4 is intended to be updated to 4.2.x when this is released and found
  to work.
  [maurits]

- Fix: to disable the secret-file authentication, an empty parameter should be
  passed to varnishd on startup.
  [fredvd, nutjob4life]


2.0a4 (2016-02-23)
------------------

- New: add option for secret-file in the script part so you can communicate to
  varnish with varnishadm. See docs for usage and secret-file generation.
  [fredvd]

- Fix: Split at max on two ':' to get a max of 3 parts as raw_backends
  [jensens]


2.0a3 (2015-12-22)
------------------

- re-release: 2.0a2 was a brown bag release
  [jensens]

2.0a2 (2015-12-22)
------------------

- Fix daemon location of script part of the recipe (/usr/bin/varnishd was
  always used.
  [fredvd]

- Fix tests,  download Varnish 4.0.3 as download.
  [fredvd]

2.0a1 (2015-03-02)
------------------

- refactoring and cleanup of the whole recipe and vcl generation:

  - skip support of varnish < v4.0, use 1.x series for older varnish support.
  - do not generate vcl code in python
  - use jinja2 templates for vcl
  - refactor vcl generation out in own testable class
  - change fixup cookies into a cookie whitelist
  - split up recipe in 3 parts: build, configuration generation and script
    generation.

  [jensens]


1.4 (unreleased)
----------------

- Fix test for running in the Varnish 2 or later.
  [cleberjsantos]

- Fixup VCL template Varnish 3.
  [cleberjsantos]

- add saint-mode for varnish_version 3.
  [cleder, cleberjsantos]

- set a default download-url for varnish_version 3.
  [cleder]

- Fixup string concat for varnish_version 3.
  [damaestro]

- Add zope2_vhm_port to be able to explicitly define a response
  port in VHM URLs.
  [damaestro]

- Add zope2_vhm_ssl to use VHM to render https urls.
  [damaestro]

- Add zope2_vhm_ssl_port to be able to explicitly define a response
  port in VHM URLs for ssl.
  [damaestro]

- Update verbose-headers to use upstream debug example:
  https://www.varnish-cache.org/trac/wiki/VCLExampleHitMissHeader
  [damaestro]

- Add cookie-fixup to better support caching of plone conent
  and to ensure no authenticated content gets cached.
  http://developer.plone.org/hosting/varnish.html
  [damaestro]

- Update VCL templates to be more flexible.
  [damaestro]


1.3 (2013-08-21)
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
