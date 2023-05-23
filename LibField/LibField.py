import serial
import datetime
import pynmea2
import time
from datetime import datetime
import sys
import threading


def connect(port="ttyACM0", baudrate=9600):
    """
    connects serial port ang returns the serial object
    written for lunix so by default opens ttyUSB0
    (though sometimes instruments connect on ACM)

    param: port: str, port to connect
    param: baudrate: int, communication rate

    other parameters are set by default and can be addressed directly
    """

    PortComm = serial.Serial(port=port)
    PortComm.baudrate = baudrate
    PortComm.parity = serial.PARITY_NONE
    PortComm.stopbits = serial.STOPBITS_ONE
    PortComm.bytesize = serial.EIGHTBITS

    return PortComm


def read_nmea(raw_line):
    """
    reads a line from an instrument and parse it using pynmea2 library
    returns the parsed line
    """

    try:
        decoded_line = raw_line.decode("utf-8").replace("\n", "").replace("\r", "")
        parsed_line = pynmea2.parse(decoded_line)
    except:
        parsed_line = -1

    return parsed_line


def launch_GPS(port="/dev/ttyACM0", namecode="001", t0=0):
    """connects to GPS
    get nmea sentence
    saves it to file for further processing

    param: port: str, port to open
    param: baudrate: int, communication rate in baud
    """

    gps = connect(port, 115000)
    idx = 0
    collect = True
    fname = "GPSout_%s.txt" % (namecode)
    f = open(fname, "w")
    global GPS_counter
    GPS_counter = 0

    while collect == True:
        idx += 1
        parsed_line = read_nmea(gps)
        try:
            with open(fname, "a") as f:
                f.write(str(parsed_line) + "\n")
            GPS_counter += 1
            # print("GPS: %i" % counter)
        except:
            pass
    f.close()


def launch_ADCP(port="/dev/ttyUSB0", namecode="001", t0=0):
    """connects to ADCP
        sends initialisation and test commands
        store ensembles

    param: port: str, port to open
    param; baudrate: int, communication rate in bauds
    """

    ADCP = connect(port=port, baudrate=57600)
    global ADCP_counter
    ADCP_counter = 0

    # wake ADCP
    lfname = "ADCP_test_log_%s.txt" % (namecode)
    f = open(lfname, "w")
    f.write("#ADCP test log\n")
    f.close()
    ADCP.send_break(0.4)
    response = True

    while response:
        if ADCP.in_waiting > 0:
            raw_line = ADCP.read(ADCP.in_waiting).decode("latin-1")
            with open(lfname, "a") as f:
                f.write(raw_line + "\n")
        else:
            if ADCP_counter >= 10:
                response = False
            else:
                ADCP_counter += 1
                time.sleep(0.2)

    # perform tests
    ordres = [
        b"ps0\r",
        b"ps3\r",
        b"pc2\r",
    ]

    for ordre in ordres:
        ADCP.write(ordre)
        with open(lfname, "a") as f:
            f.write("Command:" + str(ordre) + "\n")
        response = True
        t0 = time.time()
        while response:
            if ADCP.in_waiting > 0:
                line = ADCP.read(ADCP.in_waiting).decode("latin-1")
                with open(lfname, "a") as f:
                    f.write(line + "\n")
                print(time.time() - t0)
                ADCP_counter += 1
            # if ADCP_counter % 200 == 0:
            #     response = False
            #     time.sleep(0.1)

    dfname = "ADCP_data_%s.txt" % (str(int(t0)))
    f = open(dfname, "w")
    f.write("#ADCP raw Data file")
    f.close()


def launch_PA500(port="/dev/ttyUSB0", namecode="001"):
    """Connects to a PA500 using USBserial connection
       collects nmea sentences
       saves them to file adding t-t0 timestamp and dateime.now()

    param: port: string name of the port to open
    """

    PA500 = connect("/dev/ttyUSB0")
    global PA_counter
    PA_counter = 0
    
    response = True
    t0 = time.time()
    oldT = t0
    bad_value = 0
    fname = "PA500_%s.csv" % (namecode)
    f = open(fname, "w")
    f.write("# PA500 nmea sentence + t-t0 + datetime.now\n")
    f.close()

    while response:
        if PA500.in_waiting > 0:
            raw_line = PA500.read(40).decode("latin-1").strip("\r").strip("\n")
            t = time.time()
            now = datetime.now()
            try:
                # only keep two records per seconds
                if t - oldT > 0.5:
                    with open(fname, "a") as f:
                        f.write("%s,%s,%s\n" % (raw_line, t - t0, now))
                    oldT = t
                    PA_counter += 1
                else:
                    bad_value += 1
            except:
                print("Conversion problem. Probable incomplete serail reading")


if __name__ == "__main__":

    """Create threads one for each instrument
       Create them as daemon so that when we decide to stop acquisition
    all thread are killed (We do not use join)
    """

    GPS = threading.Thread(target=launch_GPS, args=("/dev/ttyACM0",), daemon=True)
    PA500 = threading.Thread(target=launch_PA500, args=("/dev/ttyUSB0",), daemon=True)
    ADCP = threading.Thread(target=launch_ADCP, args=("/dev/ttyUSB1",), daemon=True)

    for i in range(200):
        print("ADCP: ", ADCP_counter)
        print("PA500: ", PA_counter)
        print("GPS: ", GPS_counter)
        time.sleep(1)
