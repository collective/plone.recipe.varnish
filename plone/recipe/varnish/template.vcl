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
        pass;
    }
    if (req.http.Expect) {
        pass;
    }
    if (req.http.If-None-Match) {
        pass;
    }
    lookup;
}

sub vcl_hit {
    if (req.request == "PURGE") {
        purge_url(req.url);
        error 200 "Purged";
    }
    if (!obj.cacheable) {${header_hit_notcacheable}
        pass;
    }${header_hit_deliver}
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
    insert;
}

sub vcl_hash {
    set req.hash += req.url;
    set req.hash += req.http.host;

    if (req.http.Accept-Encoding ~ "gzip") {
        set req.hash += "gzip";
    }
    else if (req.http.Accept-Encoding ~ "deflate") {
        set req.hash += "deflate";
    }

    hash;
}

