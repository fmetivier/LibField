import serial
import datetime
import pynmea2
import time
import sys
import threading
from datetime import datetime
from bottle import route, run, template

# globals
ADCP_counter = 0
GPS_counter = 0
PA_counter = 0


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

def launch(instrument = None, port = None, t0=0, dirname='./'):
	"""
	launching function that depends only on isntrument type
	"""
	if instrument == 'Ublox':
		get_GPS(port, t0, dirname)
	elif instrument == 'ADCP':
		get_ADCP(port, t0, dirname)
	elif instrument == "PA500":
		get_PA500(port, t0, dirname)

def get_GPS(serial_port="/dev/ttyACM0", t0=0, dirname="./"):
    """connects to GPS
    get nmea sentence
    saves it to file for further processing

    param: serial_port: str, port to open
    param: baudrate: int, communication rate in baud
    param: t0: int local start time
    """

    print(serial_port, type(serial_port), len(serial_port))
    gps = connect(port=serial_port, baudrate=115000)
    # gps = connect(port="/dev/ttyACM0",baudrate=115000)
    mylog("GPS connected")
    global GPS_counter

    idx = 0
    collect = True
    fname = dirname + "GPSout_%s.txt" % (str(t0))
    f = open(fname, "w")

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


def get_ADCP(serial_port="/dev/ttyUSB1", t0=0, dirname="./"):
    """connects to ADCP
        sends initialisation and test commands
        store ensembles

    param: serial_port: str, serial port to open
    param: baudrate: int, communication rate in bauds
    param: t0: int local start time
    """

    print(serial_port)
    ADCP = connect(port=serial_port, baudrate=57600)
    # ADCP = connect(port="/dev/ttyUSB0", baudrate=57600)
    mylog("ADCP connected")
    global ADCP_counter

    # wake ADCP
    lfname = dirname + "ADCP_test_log_%s.txt" % (str(t0))
    f = open(lfname, "w")
    f.write("#ADCP test log\n")
    f.close()
    ADCP.send_break(0.4)
    response = True

    while response:
        if ADCP.in_waiting > 0:
            raw_line = ADCP.read(ADCP.in_waiting).decode("latin-1")
            with open(lfname, "a") as f:
                f.write(raw_line)
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
        response = True
        it0 = time.time()  # internal t0
        while response:
            if ADCP.in_waiting > 0:
                line = ADCP.read(ADCP.in_waiting).decode("latin-1")
                with open(lfname, "a") as f:
                    f.write(line)
                ADCP_counter += 1
            if time.time() - it0 > 10:
                response = False

    dfname = dirname + "ADCP_data_%s.txt" % (str(t0))
    f = open(dfname, "w")
    f.write("#ADCP raw Data file")
    f.close()


def get_PA500(serial_port="/dev/ttyUSB0", t0=0, dirname="./"):
    """Connects to a PA500 using USBserial connection
       collects nmea sentences
       saves them to file adding t-t0 timestamp and dateime.now()

    param: serial_port: string name of the port to open
    param: t0: int local start time
    """

    print(serial_port)
    PA500 = connect(port=serial_port)
    # PA500 = connect(port="/dev/ttyUSB1")
    mylog("PA500 connected")
    global PA_counter

    response = True
    oldT = t0
    bad_value = 0
    fname = dirname + "PA500_%s.txt" % (str(t0))
    f = open(fname, "w")
    f.write("#t-t0, datetime.now, Depth (m)\n")
    f.close()

    while response:
        if PA500.in_waiting > 0:
            raw_line = PA500.read(42).decode("latin-1")
            t = time.time()
            now = datetime.now()
            try:
                # only keep two records per seconds
                #                if t - oldT > 0.5:
                data = raw_line.split(",")
                if data[4] == "M":
                    with open(fname, "a") as f:
                        f.write("%s,%s,%s\n" % (t - t0, now, data[3]))
                    PA_counter += 1
                #                    oldT = t

                else:
                    bad_value += 1
            except:
                print("Conversion problem. Probable incomplete serail reading")

def mylog(sentence =""):

    print(sentence)
    # f = open("/home/pi/Documents/logfile.txt",a)
    # f.write(str(datetime.now()) + ":" + sentence +"\n")
    # f.close()
