import threading as th
import time
import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.append("/home/metivier/Nextcloud/src/LibField/")
import LibField as LF


def start_survey():

    # connect instruments
    # beware to check the ports before starting the survey
    #
    ADCP = LF.instrument("/dev/ttyUSB0", baudreate=57600)
    PA500 = LF.instrument("/dev/ttyUSB1", baudreate=9600)
    GPS = LF.instrument("/dev/ttyUSB2", baudreate=9600)

    # initialize ADCP

    # start acquisition
    while acquire:

        # wait for ADCP ensemble
        # check time
        # get PA
        # get GPS
        # parse PA and GPS
        # store data

        pass


def test():
    t0 = time.time()
    while acquire:
        t = time.time() - t0
        y = np.cos(t / (20 * np.pi))
        print(t, y)

        time.sleep(2)


if __name__ == "__main__":

    acquire = False
    run = True
    while run:
        choice = input("S to start acquisition, Q to stop aquisition, F to finish \n")
        if choice == "S":
            # check if not running
            if acquire == False:
                acquire = True
                th.Thread(target=test).start()
            else:
                print("Acquisition already started")
        elif choice == "Q":
            acquire = False
        elif choice == "F":
            acquire = False
            run = False
