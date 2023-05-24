import os
import sys

# sys.path.append("/home/metivier/Nextcloud/src/LibField/")
sys.path.append("/home/pi/Documents/LibField/")

for instrument in ["GPS", "PA500", "ADCP"]:
    command = (
        "python3 /home/pi/Documents/LibField/RunScripts/Run_one.py %s &" % instrument
    )
    os.system(command)
