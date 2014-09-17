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

    # Allow a grace period for offering "stale" data in case backend lags
    # https://www.varnish-cache.org/docs/3.0/tutorial/handling_misbehaving_servers.html#misbehaving-servers
    if (req.backend.healthy) {
       set req.grace = 120s;
    } else {
       set req.grace = 1h;
    }

    if (req.request == "PURGE") {
            if (!client.ip ~ purge) {
                    error 401 "Not allowed.";
            }
            ban("req.url ~ " + req.url);
            error 200 "PURGED";
    }

    if (req.request == "BAN") {
            # Same ACL check as above:
            if (!client.ip ~ purge) {
                    error 405 "Not allowed.";
            }
            ban("req.url ~ " + req.url);
            # Throw a synthetic page so the
            # request won't go to the backend.
            error 200 "Ban added";
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

    if (req.url ~ "createObject") {
        return(pass);
    }

    if (req.http.Expect) {
        return(pipe);
    }

    if (req.http.If-None-Match && !req.http.If-Modified-Since) {
        return(pass);
    }

    /* Do not cache other authorized content */
    if (req.http.Authenticate || req.http.Authorization) {
        return(pass);
    }


    remove req.http.Accept-Encoding;
${vcl_plone_cookie_fixup}

    return(lookup);
}

sub vcl_pipe {
${vcl_pipe}
    # This is not necessary if you do not do any request rewriting.
    set req.http.connection = "close";
}

sub vcl_hit {
${vcl_hit}
    if (req.request == "PURGE") {
        purge;
        set req.request = "GET";
        set req.http.X-purger = "Purged";
        error 200 "Purged. in hit " + req.url;
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
${vcl_fetch_saint}

    if (req.url ~ "createObject") {
        return(hit_for_pass);
    }

    set beresp.grace = 1h;

    return (deliver);
}

sub vcl_deliver {
${vcl_deliver_verbose}
${vcl_deliver}
    return(deliver);
}

