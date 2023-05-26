import threading
import time
import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.append("/home/pi/Documents/LibField/")
# sys.path.append("/home/metivier/Nextcloud/src/LibField/")
import LibField as LF


"""Create threads one for each instrument
Create them as daemon so that when we decide to stop acquisition all thread are killed (We do not use join)
"""


t0 = int(time.time())
ADCP_counter = 0
PA_counter = 0
GPS_counter = 0

DIRNAME = "/home/pi/Documents/Mayotte/Data/"

GPS = threading.Thread(
    target=LF.launch_GPS, args=("/dev/ttyACM0", t0, DIRNAME), daemon=True
)

PA500 = threading.Thread(
    target=LF.launch_PA500, args=("/dev/ttyUSB0", t0, DIRNAME), daemon=True
)

ADCP = threading.Thread(
    target=LF.launch_ADCP, args=("/dev/ttyUSB1", t0, DIRNAME), daemon=True
)

GPS.start()
PA500.start()
ADCP.start()

for i in range(60):
    print("time elapsed", time.time() - t0)
    print("ADCP: ", ADCP_counter)
    print("PA500: ", PA_counter)
    print("GPS: ", GPS_counter)
    time.sleep(1)
