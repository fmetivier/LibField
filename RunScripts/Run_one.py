import time
import sys
import os

sys.path.append("/home/pi/Documents/LibField/")
sys.path.append("/home/pi/Documents/SerialDeviceRetriever/")

import SerialDeviceRetriever as sdr
import LibField as LF


ld = sdr.list_devices()
man_dic = {"Ublox": "u-blox", "PA500": "Prolific", "ADCP": "FTDI"}


# launch acquisition
try:
	if len(sys.argv) > 1:
		print(sys.argv[1])
		for d in ld:
			if man_dic[sys.argv[1]] in d["manufacturer"]:
				port = "/dev/" + d["name"]
				print("on", man_dic[sys.argv[1]], port)
				LF.launch(sys.argv[1], port, sys.argv[2], sys.argv[3])
	else:
		print(
			"At present argument must be one of the followng: Ublox, PA500, ADCP"
		)
except:
    print("error")
