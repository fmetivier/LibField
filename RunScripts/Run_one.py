import time
import sys
import os

sys.path.append("/home/pi/Documents/LibField/")

import LibField as LF

t0 = int(time.time())
ADCP_counter = 0
PA_counter = 0
GPS_counter = 0

# targat data directory
DIRNAME = "/home/pi/Documents/Mayotte/Data/"
if os.path.isdir(DIRNAME) == False:
    os.mkdirs(DIRNAME)

f = open(DIRNAME + "last_t0.txt", "w")
f.write("%i" % (t0))
f.close()


# launch acquisition
try:
    if len(sys.argv) > 1:
        print(sys.argv[1])
        if sys.argv[1] in ["GPS", "PA500", "ADCP"]:
            if sys.argv[1] == "GPS":
                LF.launch_GPS("/dev/ttyACM0", t0, DIRNAME)
            elif sys.argv[1] == "PA500":
                LF.launch_PA500("/dev/ttyUSB0", t0, DIRNAME)
            elif sys.argv[1] == "ADCP":
                LF.launch_ADCP("/dev/ttyUSB1", t0, DIRNAME)
        else:
            print("argument must be one of the followng: GPS, PA500, ADCP")
except:
    print("Error: maybe check your syntax: python Run.py XXX")
    print("XXX must be one of the followng: GPS, PA500, ADCP")
