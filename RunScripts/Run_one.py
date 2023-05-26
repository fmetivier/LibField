import time
import sys
import os

sys.path.append("/home/pi/Documents/LibField/")
sys.path.append("/home/pi/Documents/SerialDeviceRetriever/")

import SerialDeviceRetriever as sdr
import LibField as LF


ld = sdr.list_devices()
t0 = int(time.time())
ADCP_counter = 0
PA_counter = 0
GPS_counter = 0

# target data directory
DIRNAME = "/home/pi/Documents/Mayotte/Data/"
if os.path.isdir(DIRNAME) == False:
    os.mkdirs(DIRNAME)

f = open(DIRNAME + "last_t0.txt", "w")
f.write("%i" % (t0))
f.close()


man_dic = {"Ublox":"u-blox","PA500":"Prolific","ADCP":"FTDI"}

	
# launch acquisition
try:
	if len(sys.argv) > 1:
		for d in ld:
			if man_dic[sys.argv[1]] in d["manufacturer"]:
				port = "/dev/" + d["name"]
				print("on", man_dic[sys.argv[1]], port, type(port), len(port))
				LF.launch(sys.argv[1],port, t0, DIRNAME)
			else:
				print("At present argument must be one of the followng: Ublox, PA500, ADCP")
except:
	print("Error: maybe check your syntax: python Run.py XXX")
	print("XXX must be one of the followng: GPS, PA500, ADCP")
