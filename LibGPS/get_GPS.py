import serial
import datetime
import pynmea2
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def connect_gps(gps_port="ttyUSB0", gps_baudrate=9600):
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
    gps = connect_gps("/dev/ttyUSB0")
    idx = 0

    while True:
        idx += 1
        parsed_line = read_nmea(gps)
        try:
            print("########################")
            print(parsed_line.sentence_type)
            print("########################")
            for field in parsed_line.fields:
                value = getattr(parsed_line, field[1])
                print(f"{field[0]:40} {field[1]:20} {value}")
        except:
            pass
