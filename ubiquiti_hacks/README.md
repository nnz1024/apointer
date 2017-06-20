# Some useful hacks for using Ubiquiti devices on long distances

## Remove default SNMP caching on Ubiquiti devices

By default, all SNMP variables are updated with 16 seconds period, see
https://community.ubnt.com/t5/airFiber/SNMP-RSSI-Refresh-rate/td-p/297932

This is inappropriate if you want to get actual signal level every second.
Given script `rc.poststart` removes `cache` parameter from `/etc/tinysnmpd.conf`
and restarts `tinysnmpd` at every boot (this is much simpler than editing this
file in root image and flashing this image to every device).

1. Upload `rc.poststart` to device's `/etc/persistent/`, e.g.
```
    scp rc.poststart ubnt@192.168.1.20:/etc/persistent/
```
2. On device, grant execute permission to this script, save changes and reboot:
```
    chmod +x /etc/persistent/rc.poststart && cfgmtd -w -p /etc/ && reboot
```

Use `../standalone_tests/test_snmp.pl` to make sure it works.

## One-channel mode

Ubiquiti devices with MIMO (such as Rocket M5) may require to use two channels,
i.e. antenna polarizations. Since horizontal polarization fades with distance
faster than vertical one (when the signal propagates near to the ground, i.e.
at small angles to the horizon), there can be some problems with MIMO on
long distances. In this case, uncomment lines 9-12 in `rc.poststart` before
uploading, and use modulation and coding schemas (MCS) from 1 to 7.
