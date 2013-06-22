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

${vcl_recv}

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
${vcl_pipe}
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
    set beresp.grace = 120s;
${vcl_fetch}
    if (!beresp.ttl > 0s) {${header_fetch_notcacheable}
        return(hit_for_pass);
    }
    if (beresp.http.Set-Cookie) {${header_fetch_setcookie}
        return(hit_for_pass);
    }
    if (beresp.http.Cache-Control ~ "(private|no-cache|no-store)") {${header_fetch_cachecontrol}
        return(hit_for_pass);
    }
    if (beresp.http.Authorization && !beresp.http.Cache-Control ~ "public") {${header_fetch_auth}
        return(hit_for_pass);
    }
    ${header_fetch_insert}
}

sub vcl_deliver {
${vcl_deliver}
}
