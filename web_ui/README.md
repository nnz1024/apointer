# HTML5/AJAX web user interface

Web UI for `tracker.py` requires a web server (e.g. NGINX) which serves 
`ui_*.html` directly to client, but forwards `/tracker/*` locations to port 8000
on host which runs `tracker.py`, e.g.

    location /tracker/ {
        proxy_pass http://127.0.0.1:8000;
    }

These requests will be served by `tracker.py`. By default it listens 
`127.0.0.1:8000`, so it can get requests only from its host. If you want to 
place web UI on different host, don't forget to change listen address in 
`[HTTP]` section of `main.ini` config file (listen port can be altered as well).

Script `test_httpserver.py` allows to test some basic functions of web UI, viz.
connecting with server, receiving and displaying of azimuth, elevation and
signal level, in text form and on a graphical diagram. It cyclically generates
the helical (clockwise) path starting at the zenith and finishing at the north
point of the horizon, simultaneously with the decreasing of the signal level
from 0 to -90 dBm. Please note that it *will not work* without properly 
configured web server (see above), and, moreover, when you open `ui_*.html`
from a local folder instead of using a web server.
