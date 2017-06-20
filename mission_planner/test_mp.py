# -*- coding: cp1251 -*-
print "Starting..."
print "Waiting for GPS..."
while (cs.lat == 0):
	Script.Sleep(1000)
print "Got GPS!"
fi = open(u"C:\mps_test.txt", "w")
for it in range(1, 201):
        fi.write("cnt={0:3d}; lat={1:10.6f}; lng={2:10.6f}; alt={3:8.1f}\r\n".
                 format(it, cs.lat, cs.lng, cs.altoffsethome))
        if ((it % 10) == 0):
                fi.flush()
                print("{0:3d} points saved".format(it))
        Script.Sleep(10000)
fi.close()
print "Done!"
