import os
import sys
import time


# sys.path.append("/home/metivier/Nextcloud/src/LibField/")
sys.path.append("/home/pi/Documents/LibField/")

t0 = int(time.time())

# target data directory
DIRNAME = "/home/pi/Documents/Mayotte/Data/"
if os.path.isdir(DIRNAME) == False:
    os.mkdirs(DIRNAME)

f = open(DIRNAME + "last_t0.txt", "w")
f.write("%i" % (t0))
f.close()

#
for instrument in ["Ublox", "PA500", "ADCP"]:
    command = "python3 /home/pi/Documents/LibField/RunScripts/Run_one.py %s %s %s &" % (
        instrument,
        t0,
        DIRNAME,
    )
    print(command)
    os.system(command)

#finally launch website
# os.system("python3 /home/pi/Documents/LibField/LibField/WebLib.py &")
