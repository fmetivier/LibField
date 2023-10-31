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


def read_nmea(instrument):
    """
    reads a line from a GPS and parse it using pynmea2 library
    returns the parsed line

    :param instrument: gps serial connection object
    :return: parsed line
    """

    try:
        raw_line = instrument.readline()
        decoded_line = raw_line.decode(
            "utf-8").replace("\n", "").replace("\r", "")
        parsed_line = pynmea2.parse(decoded_line)
    except:
        parsed_line = -1

    return parsed_line


def launch(instrument=None, port=None, t0=0, dirname="./"):
    """
    launching function that depends only on instrument type
    """
    if instrument == "Ublox":
        get_GPS(port, t0, dirname)
    elif instrument == "ADCP":
        get_ADCP(port, t0, dirname)
    elif instrument == "PA500":
        get_PA500(port, t0, dirname)


def get_GPS(serial_port="/dev/ttyACM0", t0=0, dirname="./"):
    """connects to GPS
    get nmea sentence
    saves it to file for further processing

    TODO do not parse. Just dump the line.

    param: serial_port: str, port to open
    param: baudrate: int, communication rate in baud
    param: t0: int local start time
    """

    print("GPS")
    print(serial_port)
    gps = connect(port=serial_port, baudrate=115000)
    # gps = connect(port="/dev/ttyACM0",baudrate=115000)
    print("GPS connected")
    global GPS_counter

    idx = 0
    collect = True
    fname = dirname + "GPS_%s.txt" % (str(t0))
    f = open(fname, "w")

    while collect == True:
        idx += 1
        parsed_line = read_nmea(gps)
        try:
            if parsed_line != "-1\n":
                with open(fname, "a") as f:
                    f.write(str(parsed_line) + "\n")
                GPS_counter += 1
            # print("GPS: %i" % counter)
        except:
            pass
    f.close()


def get_ADCP(serial_port="/dev/ttyUSB1", t0=0, dirname="./"):
    """connects to ADCP
        sends initialisation and test commands, stores results in lfname
        sends configuration commands and starts pinging store ensembles in dfname

    param: serial_port: str, serial port to open
    param: baudrate: int, communication rate in bauds
    param: t0: int local start time
    param: dirname: str directory path
    """

    print("ADCP")
    print(serial_port)
    ADCP = connect(port=serial_port, baudrate=57600)
    # ADCP = connect(port="/dev/ttyUSB0", baudrate=57600)
    print("ADCP connected")
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

    dfname = dirname + "ADCP_%s.txt" % (str(t0))
    f = open(dfname, "w")
    f.write("#ADCP raw Data file")
    f.close()

    """
    ordres = [
        b"CR1",
        b"CF11210",
        b"EA00000", Alignement de la direction par défaut
        b"ED00000", Profondeur du transducteur par défaut
        b"ES",  salinité  en parties pour mille
        b"EX11111", transformation de coordonnées: coordonnées terrestres (Est-Nord), utilise les données de tilts, autorise une solution à trois transducteurs, autorise le bin mapping (pas compris j'ai pris le défaut)
        b"EZ1111101", Sensor source : vitesse du son calculée, profondeur itoo, heading, pitch et roll internes aussi, salinité fournie (voir ES), température mesurée en interne.
        b"WN030",   dépend de la profondeur à calculer
        b"WP00045",  nombre de ping par ensemble
        b"WS0050",  taille de cellulle 50 cm
        b"TE00:00:00.50",  temps entre les ensembles default 01:00:00.00 ici je lui dis de démarrer la mesure immédiatement
        b"TP00:00.05", delta t entre ping si 0 va aussi vite que possible.
        b"PD8",
        ajouter
        b"WM1", Profiling mode 1 (défaut). Vérifier si on a pas intérêtà utiliser le 5 ou le 8
        b"CK",
        b"CS",
    ]
    """
    ordres = [
        b"CR1\r",
        b"CF11010\r",
        b"EA00000\r",
        b"ED00000\r",
        b"ES01\r",
        b"EX00000\r",
        b"EZ1111101\r",
        b"WN010\r",
        b"WP00001\r",
        b"WS0005\r",
        b"TE00:00:00.00\r",
        b"TP00:00.50\r",
        b"PD0\r",
        b"WM1\r",
        b"CK\r",
        b"CS\r",
    ]

    ADCP.send_break(0.4)
    for ordre in ordres:
        ADCP.write(ordre)
        print(ordre.decode())
        time.sleep(0.5)

    response = True
    dt = 0.1
    while response:
        line = "\n" + str(datetime.now()) + ","
        if ADCP.in_waiting > 0:
            while ADCP.in_waiting > 0:
                line += ADCP.read().decode("latin-1")
            with open(dfname, "a") as f:
                f.write(line)
            ADCP_counter += 1
        time.sleep(dt)


def test_ADCP(serial_port="/dev/ttyUSB0"):
    """connects to ADCP


    param: serial_port: str, serial port to open
    param: baudrate: int, communication rate in bauds
    param: t0: int local start time
    param: dirname: str directory path
    """

    print("ADCP")
    print(serial_port)
    ADCP = connect(port=serial_port, baudrate=57600)

    print("ADCP connected")
    global ADCP_counter

    # wake ADCP
    ADCP.send_break(0.4)
    response = True

    line = ""
    while response:
        if ADCP.in_waiting > 0:
            raw_line = ADCP.read(ADCP.in_waiting).decode("latin-1")
            line += raw_line
        else:
            if ADCP_counter >= 10:
                response = False
            else:
                ADCP_counter += 1
                time.sleep(0.2)
    print(line)

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
        st = ""
        while response:
            if ADCP.in_waiting > 0:
                line = ADCP.read(ADCP.in_waiting).decode("latin-1")
                st += line
                ADCP_counter += 1
            if time.time() - it0 > 10:
                response = False

        print(st)

    """
    ordres = [
        b"CR1",
        b"CF11210",
        b"EA00000", Alignement de la direction par défaut
        b"ED00000", Profondeur du transducteur par défaut
        b"ES",  salinité  en parties pour mille
        b"EX11111", transformation de coordonnées: coordonnées terrestres (Est-Nord), utilise les données de tilts, autorise une solution à trois transducteurs, autorise le bin mapping (pas compris j'ai pris le défaut)
        b"EZ1111101", Sensor source : vitesse du son calculée, profondeur itoo, heading, pitch et roll internes aussi, salinité fournie (voir ES), température mesurée en interne.
        b"WN030",   dépend de la profondeur à calculer
        b"WP00045",  nombre de ping par ensemble
        b"WS0050",  taille de cellulle 50 cm
        b"TE00:00:00.50",  temps entre les ensembles default 01:00:00.00 ici je lui dis de démarrer la mesure immédiatement
        b"TP00:00.05", delta t entre ping si 0 va aussi vite que possible.
        b"PD8",
        ajouter
        b"WM1", Profiling mode 1 (défaut). Vérifier si on a pas intérêtà utiliser le 5 ou le 8
        b"CK",
        b"CS",
    ]
    """
    ordres = [
        b"CR1\r",
        b"CF11010\r",
        b"EA00000\r",
        b"ED00000\r",
        b"ES01\r",
        b"EX00000\r",
        b"EZ1111101\r",
        b"WN010\r",
        b"WP00001\r",
        b"WS0005\r",
        b"TE00:00:00.00\r",
        b"TP00:00.50\r",
        b"PD0\r",
        b"WM1\r",
        b"CK\r",
        b"CS\r",
    ]

    ADCP.send_break(0.4)
    for ordre in ordres:
        ADCP.write(ordre)
        print(ordre.decode())
        time.sleep(0.5)

    response = True
    dt = 0.1
    count = 0
    while response:
        count += 1
        line = "\n" + str(datetime.now()) + ","
        if ADCP.in_waiting > 0:
            while ADCP.in_waiting > 0:
                line += ADCP.read().decode("latin-1")
            print(line)
            ADCP_counter += 1
        time.sleep(dt)
        if count == 100:
            response = False


def get_PA500(serial_port="/dev/ttyUSB0", t0=0, dirname="./"):
    """Connects to a PA500 using USBserial connection
       collects nmea sentences
       saves them to file adding t-t0 timestamp and dateime.now()

    param: serial_port: string name of the port to open
    param: t0: int local start time
    """

    print("PA500")
    print(serial_port)
    PA500 = connect(port=serial_port)
    # PA500 = connect(port="/dev/ttyUSB1")
    print("PA500 connected")
    global PA_counter

    response = True
    oldT = float(t0)
    bad_value = 0
    fname = dirname + "PA500_%s.txt" % (str(t0))
    f = open(fname, "w")
    f.write("#t-t0, datetime.now, NMEA string\n")
    f.close()
    dt = 0.13
    raw_line = ""
    while response:
        N = PA500.in_waiting
        if N > 0:
            c = PA500.read(1).decode("latin-1")
            while c != "\n":
                raw_line += c
                c = PA500.read(1).decode("latin-1")
            t = time.time()
            now = datetime.now()
            try:
                if t - oldT > 0.5:
                    with open(fname, "a") as f:
                        f.write("%s,%s,%s\n" % (t - float(t0), now, raw_line))
                    # print(t-float(t0),now, raw_line)
                    PA_counter += 1
                    oldT = t
                # else:
                #     bad_value += 1
                raw_line = ""
            except:
                pass
            raw_line = ""


def mylog(sentence=""):

    # ~ print(sentence)
    f = open("logfile.txt", "a")
    f.write(str(datetime.now()) + ":" + sentence + "\n")
    f.close()


if __name__ == '__main__':
    test_ADCP()
