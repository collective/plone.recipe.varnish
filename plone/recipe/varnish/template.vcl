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

    return(lookup);
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
        return(pass);
    }
}

sub vcl_miss {
    if (req.request == "PURGE") {
        error 404 "Not in cache";
    }

}

sub vcl_fetch {
    set beresp.grace = 120s;
    if (!beresp.cacheable) {${header_fetch_notcacheable}
        return(pass);
    }
    if (beresp.http.Set-Cookie) {${header_fetch_setcookie}
        return(pass);
    }
    if (beresp.http.Cache-Control ~ "(private|no-cache|no-store)") {${header_fetch_cachecontrol}
        return(pass);
    }
    if (beresp.http.Authorization && !beresp.http.Cache-Control ~ "public") {${header_fetch_auth}
        return(pass);
    }
    ${header_fetch_insert}
}

