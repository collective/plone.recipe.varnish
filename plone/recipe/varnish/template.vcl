# This is a basic VCL configuration file for varnish.  See the vcl(7)
# man page for details on VCL syntax and semantics.

${backends}
acl purge {
    "localhost";
}

sub vcl_recv {
    
    ${virtual_hosting}
    
    if (req.request == "PURGE") {
        if (!client.ip ~ purge) {
            error 405 "Not allowed.";
        }
        lookup;
    }
    if (req.request != "GET" && req.request != "HEAD") {
        pipe;
    }
    if (req.http.Expect) {
        pipe;
    }
    if (req.http.If-None-Match) {
        pass;
    }
    lookup;
}

sub vcl_hit {
    if (req.request == "PURGE") {
        set obj.ttl = 0s;
        error 200 "Purged";
    }
    if (!obj.cacheable) {
        pass;
    }
    deliver;
}

sub vcl_miss {
    if (req.http.If-Modified-Since) {
        pass;
    }
    if (req.request == "PURGE") {
        error 404 "Not in cache";
    }
    fetch;
}

sub vcl_fetch {
    if (!obj.valid) {
        error;
    }
    if (!obj.cacheable) {
        pass;
    }
    if (obj.http.Set-Cookie) {
        pass;
    }
    if (obj.http.Cache-Control ~ "(private|no-cache|no-store)") {
        pass;
    }
    if (req.http.Authorization && !obj.http.Cache-Control ~ "public") {
        pass;
    }
    insert;
}
