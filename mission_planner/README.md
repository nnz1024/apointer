# Sending coordinates of the UAV to the antenna pointing system

## Scripts

* `mpsend` — Python script for MissionPlanner which sends telemetry data
(latitude, longitude and altitude) received from UAV to given IP:PORT (`addr` 
variable in script) via UDP in JSON which can be received and understanded by 
`tracker.py`. Note that it requires Python to be installed on host with 
MissionPlanner (mainly for `socket` module). Don't forget to adjust 
`sys.path.append()` line so that it could find Python modules on your system.

* `mpsend_tcp` — same for TCP. Note that TCP support was globally abandoned
later, so it **may not work** even if you replace `nsock.NSockUDP` to
`nsock.NSockTCP` in `tracker.py`.

* `test_mp` — writes data to `C:\mps_test.txt` instead of sending them.

## Data format

Message is formatted JSON-like, with the newline character as a terminator:
```
    {"lat":%.5f, "lon":%.5f, "alt":%.5f}\n
```
where three fixed-point format symbols means latitude, longitude and altitude 
correspondingly. Recommended precision is at least 5 digits after decimal point.

Format is mostly JSON-compatible, so `tracker.py` uses `json.loads()` to parse 
it. Exception is a special mean of newline character.
**As \n is a terminator symbol, do not use it in the body of the message!**

Positive latitude means North, and positive longitude means East. Negative ones
should mean South and West correspondingly, but I has no time to test it.

Example (newline character at the end was not shown):
```
    {"lat":60.75076, "lon":30.04847, "alt":200}
```

Feel free to re-implement this on the platform you need (e.g. for your on-board
controller/transmitter, or for your telemetry-receiving software).
