# This is a basic VCL configuration file for varnish.  See the vcl(7)
# man page for details on VCL syntax and semantics.

${backends}
${director}
acl purge {
	"localhost";
${purgehosts}
}

sub vcl_recv {
${vcl_recv}
${virtual_hosting}
	set req.grace = 120s;

	if (req.request == "PURGE") {
		if (!client.ip ~ purge) {
			error 405 "Not allowed.";
		}
		return(lookup);
	}

	if (req.request != "GET" &&
		req.request != "HEAD" &&
		req.request != "PUT" &&
		req.request != "POST" &&
		req.request != "TRACE" &&
		req.request != "OPTIONS" &&
		req.request != "DELETE") {
		/* Non-RFC2616 or CONNECT which is weird. */
		return(pipe);
	}

	if (req.request != "GET" && req.request != "HEAD") {
		/* We only deal with GET and HEAD by default */
		return(pass);
	}

	if (req.http.If-None-Match) {
		return(pass);
	}

	if (req.url ~ "createObject") {
		return(pass);
	}

	remove req.http.Accept-Encoding;
${vcl_plone_cookie_fixup}
}

sub vcl_pipe {
${vcl_pipe}
	# This is not necessary if you do not do any request rewriting.
	set req.http.connection = "close";
}

sub vcl_hit {
${vcl_hit}
	if (req.request == "PURGE") {
		ban_url(req.url);
		error 200 "Purged";
	}

	if (!obj.ttl > 0s) {
		return(pass);
	}
}

sub vcl_miss {
${vcl_miss}
	if (req.request == "PURGE") {
		error 404 "Not in cache";
	}

}

sub vcl_fetch {
${vcl_fetch_verbose}
${vcl_fetch}
	set beresp.grace = 120s;
}

sub vcl_deliver {
${vcl_deliver_verbose}
${vcl_deliver}
}

