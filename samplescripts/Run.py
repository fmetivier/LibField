import os
import sys

sys.path.append("/home/metivier/Nextcloud/src/LibField/")

for instrument in ['GPS','PA500','ADCP']:
    command = 'python3 Run_one.py %s &' %  instrument
    os.system(command)
