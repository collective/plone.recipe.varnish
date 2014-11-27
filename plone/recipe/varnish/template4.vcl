/*
* Marker to tell the VCL compiler that this VCL has been adapted to the
* new 4.0 format.
* Varnish now requires the first line of VCL to indicate the VCL version number:
*/

vcl 4.0;

import std;

${backends}
# Note. Add this block with logic for creation, within the __init__.py

# backend backend_0 {
#    .host = "IP HERE";
#    .port = "8081";
#    .connect_timeout = 0.4s;       # How long to wait for a backend connection?
#    .first_byte_timeout = 300s;    # How long to wait before we receive a first byte from our backend?
#    .between_bytes_timeout  = 60s; # How long to wait between bytes received from our backend?
#}
#
#backend backend_1 {
#    .host = "IP HERE";
#    .port = "8082";
#    .connect_timeout = 0.4s;
#    .first_byte_timeout = 300s;
#    .between_bytes_timeout  = 60s;
#}


/* 
Directors have been moved to the vmod_directors.
Below is a redirector based on round-robin requests
*/

# Note. Add this block with logic for creation, within the __init__.py
# {director}
import directors;

sub vcl_init {
    new cluster1 = directors.round_robin(); # A new directors for round robin defined
    cluster1.add_backend(backend_0);        # Added Backend defined above
    cluster1.add_backend(backend_1);
}


acl purge {
    "localhost";
${purgehosts}
}

sub vcl_recv {
${vcl_recv}
${virtal_hosting}
# set req.backend_hint = cluster1.backend();
# set req.backend_hint = backend_1;

    if (req.method == "PURGE") {
        # Not from an allowed IP? Then die with an error.
        if (!client.ip ~ purge) {
            return (synth(405, "This IP is not allowed to send PURGE requests."));
        }
        return(purge);
    }
    
    if (req.method == "BAN") {
            # Same ACL check as above:
            if (!client.ip ~ purge) {
            return(synth(403, "Not allowed."));
            }
            #ban("req.url ~ " + req.url);
        ban("req.http.host == " + req.http.host +
            " && req.url == " + req.url);
            # Throw a synthetic page so the
            # request won't go to the backend.
            return(synth(200, "Ban added"));
    }

    # Large static files should be piped, so they are delivered directly to the end-user without
    # waiting for Varnish to fully read the file first.
    # TODO: once the Varnish Streaming branch merges with the master branch, use streaming here to avoid locking.
    if (req.url ~ "^[^?]*\.(mp[34]|rar|tar|tgz|gz|wav|zip)(\?.*)?$") {
        unset req.http.Cookie;
        return(pipe);
    }

    # Only deal with "normal" types
    if (req.method != "GET" &&
           req.method != "HEAD" &&
           req.method != "PUT" &&
           req.method != "POST" &&
           req.method != "TRACE" &&
           req.method != "OPTIONS" &&
           req.method != "DELETE") {
        /* Non-RFC2616 or CONNECT which is weird. */
        return(pipe);
    }

    # Only cache GET or HEAD requests. This makes sure the POST requests are always passed.
    if (req.method != "GET" && req.method != "HEAD") {
        # Dont't cache POST
        if (req.method == "POST") {
            return(pass);
        }

        # Dont't cache createObject
        if (req.url ~ "createObject") {
            return(pass);
        }

        return(pass);
    }

    if (req.http.Expect) {
        return(pipe);
    }

    if (req.http.If-None-Match && !req.http.If-Modified-Since) {
        return(pass);
    }

    /* Do not cache other authorized content by default */
    if (req.http.Authenticate || req.http.Authorization) {
        return(pass);
    }

${vcl_plone_cookie_fixup}

    return(hash);
}

sub vcl_pipe {
${vcl_pipe}
    # By default Connection: close is set on all piped requests, to stop
    # connection reuse from sending future requests directly to the
    # (potentially) wrong backend. If you do want this to happen, you can undo
    # it here.
    # unset bereq.http.connection;

    return(pipe);
}

sub vcl_pass {
    return (fetch);
}

sub vcl_purge {
    return (synth(200, "Purged"));
}

sub vcl_hit {
${vcl_hit}
    if (obj.ttl >= 0s) {
        // A pure unadultered hit, deliver it
        # normal hit
        return (deliver);
    }
    
    # We have no fresh fish. Lets look at the stale ones.
    if (std.healthy(req.backend_hint)) {
        # Backend is healthy. Limit age to 10s.
        if (obj.ttl + 10s > 0s) {
            set req.http.grace = "normal(limited)";
            return (deliver);
        } else {
            # No candidate for grace. Fetch a fresh object.
            return(fetch);
        }
    } else {
        # backend is sick - use full grace
        // Object is in grace, deliver it
        // Automatically triggers a background fetch
        if (obj.ttl + obj.grace > 0s) {
            set req.http.grace = "full";
            return (deliver);
        } else {
            # no graced object.
            return (fetch);
        }
    }
    
    if (req.method == "PURGE") {
        set req.method = "GET";
        set req.http.X-purger = "Purged";
        return(synth(200, "Purged. in hit " + req.url));
    }
    
    // fetch & deliver once we get the result
    return (fetch);
}

sub vcl_miss {
${vcl_miss}
    if (req.method == "PURGE") {
        set req.method = "GET";
        set req.http.X-purger = "Purged-possibly";
        return(synth(200, "Purged. in miss " + req.url));
    }

    // fetch & deliver once we get the result
    return (fetch);
}

sub vcl_backend_fetch{
    return (fetch);
}

sub vcl_backend_response {
${vcl_backend_response_verbose}
${vcl_backend_response}
    if (beresp.ttl <= 0s
        || beresp.http.Set-Cookie
        || beresp.http.Surrogate-control ~ "no-store"
        || (!beresp.http.Surrogate-Control && beresp.http.Cache-Control ~ "no-cache|no-store|private")
        || beresp.http.Vary == "*") {
            /* * Mark as "Hit-For-Pass" for the next 2 minutes */
            set beresp.ttl = 120s;
            set beresp.uncacheable = true;

    if (beresp.status >= 500 && beresp.status < 600) {
        unset beresp.http.Cache-Control;
        set beresp.http.X-Cache = "NOCACHE";
        set beresp.http.Cache-Control = "no-cache, max-age=0, must-revalidate";
        set beresp.ttl = 0s;
        set beresp.http.Pragma = "no-cache";
        set beresp.uncacheable = true;
        return(deliver);
    }

    if (bereq.url ~ "createObject") {
        set beresp.uncacheable = true;
        return(deliver);
    }

    set beresp.grace = 1h;

    return (deliver);
}

sub vcl_deliver {
    set resp.http.grace = req.http.grace;
${vcl_deliver_verbose}
${vcl_deliver}
}

/*
 We can come here "invisibly" with the following errors: 413, 417 & 503
*/
sub vcl_synth {
    set resp.http.Content-Type = "text/html; charset=utf-8";
    set resp.http.Retry-After = "5";
    
    synthetic( {"
        <?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
          <head>
            <title>"} + resp.status + " " + resp.reason + {"</title>
          </head>
          <body>
            <h1>Error "} + resp.status + " " + resp.reason + {"</h1>
            <p>"} + resp.reason + {"</p>
            <h3>Guru Meditation:</h3>
            <p>XID: "} + req.xid + {"</p>
            <hr>
            <p>Varnish cache server</p>
          </body>
        </html>
    "} );

    return (deliver);
}
