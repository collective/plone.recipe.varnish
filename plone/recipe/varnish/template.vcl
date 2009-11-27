# This is a basic VCL configuration file for varnish.  See the vcl(7)
# man page for details on VCL syntax and semantics.

${backends}
${director}
acl purge {
	"localhost";
${purgehosts}
}

sub vcl_recv {
	set req.grace = 120s;
	${virtual_hosting}
	
	if (req.request == "PURGE") {
		if (!client.ip ~ purge) {
			error 405 "Not allowed.";
		}
		lookup;
	}

	if (req.request != "GET" &&
		req.request != "HEAD" &&
		req.request != "PUT" &&
		req.request != "POST" &&
		req.request != "TRACE" &&
		req.request != "OPTIONS" &&
		req.request != "DELETE") {
		/* Non-RFC2616 or CONNECT which is weird. */
		pipe;
	}

	if (req.request != "GET" && req.request != "HEAD") {
		/* We only deal with GET and HEAD by default */
		pass;
	}

	if (req.http.If-None-Match) {
		pass;
	}

	if (req.url ~ "createObject") {
		pass;
	}

	remove req.http.Accept-Encoding;

	lookup;
}

sub vcl_pipe {
	# This is not necessary if you do not do any request rewriting.
	set req.http.connection = "close";
}

sub vcl_hit {
	if (req.request == "PURGE") {
		purge_url(req.url);
		error 200 "Purged";
	}

	if (!obj.cacheable) {
		pass;
	}
}

sub vcl_miss {
	if (req.request == "PURGE") {
		error 404 "Not in cache";
	}

}

sub vcl_fetch {
	set obj.grace = 120s;
	if (!obj.cacheable) {${header_fetch_notcacheable}
		pass;
	}
	if (obj.http.Set-Cookie) {${header_fetch_setcookie}
		pass;
	}
	if (obj.http.Cache-Control ~ "(private|no-cache|no-store)") {${header_fetch_cachecontrol}
		pass;
	}
	if (req.http.Authorization && !obj.http.Cache-Control ~ "public") {${header_fetch_auth}
		pass;
	}
	${header_fetch_insert}
}

