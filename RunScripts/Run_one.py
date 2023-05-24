import threading
import time
import sys

sys.path.append("/home/metivier/Nextcloud/src/LibField/")

import LibField as LF

t0 = int(time.time())
ADCP_counter = 0
PA_counter = 0
GPS_counter = 0
DIRNAME = "/home/pi/Documents/Mayotte/Data"

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
    print("Error: check your syntax: python Run.py XXX")
    print("XXX must be one of the followng: GPS, PA500, ADCP")
