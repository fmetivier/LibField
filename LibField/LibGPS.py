import serial
import datetime
import pynmea2
import time


def connect_gps(gps_port="ttyACM0", gps_baudrate=115000):
    """
    connects to the GPS using serial ang returns the serial object
    written for lunix so by default opens ttyUSB0
    (though sometimes GPS connect on ACM)
    """
    ser = serial.Serial(port=gps_port, baudrate=gps_baudrate)
    # reset everything and skip first line
    ser.flushInput()
    ser.flushOutput()
    ser.readline()
    return ser


def read_nmea(gps):

    try:
        raw_line = gps.readline()
        decoded_line = raw_line.decode("utf-8").replace("\n", "").replace("\r", "")
        parsed_line = pynmea2.parse(decoded_line)
    except:
        parsed_line = -1

    return parsed_line


if __name__ == "__main__":
    gps = connect_gps("/dev/ttyACM0")
    idx = 0
    collect = True
    fname = "GPSout_%s.txt" % (str(int(time.time())))
    f = open(fname, "w")
    while collect == True:
        idx += 1
        parsed_line = read_nmea(gps)
        try:
            data = str(parsed_line).split(",")
            print(str(parsed_line))
            f.write(str(parsed_line) + "\n")
            for field in parsed_line.fields:
                value = getattr(parsed_line, field[1])
                print("%s,%s" % (str(field[1]), value))
                f.write("%s,%s\n" % (str(field[1]), value))
        except:
            pass
    f.close()
