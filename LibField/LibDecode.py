import sys
import numpy as np
import datetime
import pynmea2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class ADCPEnsemble:
    """Class to process ADCP ensembles
    """

    def __init__(self, Header, FixLeader, VariableLeader, Data, BottomTrack):
        """Class initialisation

        :param Header: dic containing header data
        :param FixLeader: dic containing fix leader data
        :param VariableLeader: dic containing variable leader data
        :param Data: value for key, value in variable}: dic containing velocity and intensity data
        :param BottomTrack: dic containing bottom track data

        """
        self.Header = Header
        self.FixLeader = FixLeader
        self.VariableLeader = VariableLeader
        self.Data = Data
        self.BottomTrack = BottomTrack

        # process ADCP ensemble
        # transform velocities
        self.VADCP = self.Beam2xyz()
        self.VGeo = self.ADCP2Geog()

    def SoundVel(T=0.0, S=0.0, D=0.0):
        """ returns the spead of sound for a given temperature, salinity and depth

        :param T: float, temperature in degrees C
        :param S: float, Salinity in parts per thousands  (or g/l)
        :param D: float, depth in meters

        :returns: vs calculated speed of sound
        :rtype: float
        """

        vs = 1449.2 + 4.6*T - 0.055*T**2 + 0.00029 * \
            T**3 + (1.34-0.01*T)*(S-35) + 0.016*D

        return vs

    def TransposeVel(self, V=None):
        """returns the velocity along component comp
        depending on the acquisition procedure this can be a beam radial velocity or an earth referenced velocity.

        :param comp: velocity component to return
        """
        if V:
            return np.transpose(np.array(V))
        else:
            return None

    def Beam2xyz(self):
        """Transform beam velocities XYZ velocities

        checks for cells with
        uses all four beams to calculate vz.
        nor error calculation at that point

        returns z, vx,vy,vz
        """

        VADCP = []
        BA = 20*np.pi/180
        for v, pg, z in zip(self.Data["Velocity"], self.Data["Percent Good"], self.Data["Depth"]):
            if np.sum(pg) == 400 and -32768 not in v:
                vx = (v[0]-v[1])/(2*np.sin(BA))
                vy = (v[3]-v[2])/(2*np.sin(BA))
                vz = np.sum(v)/(4*np.cos(BA))
                e = (v[0]+v[1]-v[2]-v[3])/(2*np.sqrt(2)*np.sin(BA))
                VADCP.append([z, vx, vy, vz, e])
            else:
                pass
        return VADCP

    def ADCP2Geog(self):
        """Transform velocity referenced to boat by applying heading rotation"""
        tr = self.VariableLeader["ER"] * np.pi / 18000
        tp = np.arctan(
            np.tan(self.VariableLeader["EP"] * np.pi / 18000)*np.cos(tr))
        th = self.VariableLeader["EH"] * np.pi / 18000

        TR = np.array([[np.cos(tr), 0, np.sin(tr)], [
                      0, 1, 0], [-np.sin(tr), 0, np.cos(tr)]])

        TP = np.array([[1, 0, 0], [0, np.cos(tp), np.sin(tp)],
                      [0, -np.sin(tp), np.cos(tp)]])

        TH = np.array([[np.cos(th), np.sin(th), 0],
                      [-np.sin(th), np.cos(th), 0], [0, 0, 1]])

        M = np.dot(TH, np.dot(TP, TR))

        VGeo = []
        for d in self.VADCP:
            v = np.array([d[1], d[2], d[3]])
            vg = np.dot(M, v)
            VGeo.append([d[0], vg[0], vg[1], vg[2]])

        return VGeo

    def Geog2earth(self, tt='GPS'):
        """Transform Geographical velocity in an earth reference by substracting boat velcity vector depending on tt value  applies bottom tracking using the echosounder or the BT values or uses RTK GPS values

        :param tt: str GPS or BT or PA
            GPS: perform RTK GPS calculation of boat velocity
            BT: perform BT velocity measurement of boat using ADCP only
            PA: perform BT velocity measurement of boat using echosounder to find the bottom cell.
        """
        pass

    def GV(self, comp=1):
        """returns the good velocity along component comp
        depending on the acquisition procedure this can be a beam radial velocity or an earth referenced velocity.

        :param comp: velocity component to return
        """

        V_array = np.transpose(np.array(self.Data["Velocity"]))
        G_array = np.transpose(np.array(self.Data["Percent Good"]))
        V = V_array[comp]
        G = G_array[comp]
        V[V == -32768] = 0
        V[G <= 0] = 0
        return (V)

    def avg_V(self, type='Cell'):
        if type == "Cell":
            pass
        elif type == "Profile":
            pass


def Process_Ensemble(Line, LN=1, out=False):
    """Decodes an ADCP Ensemble
    - Header, Fix Leader, Variable Leader and Bottom Track are decoded here
    because they have unique series of parameters
    - Velocity, Correlation Intensity, Echo Intensity, Percent made good are decoded using read_data function

    :param Line: hexascii bytes, the ensemble
    :param LN: int, Line number

    """

    ######################################################
    #
    # Lists and dics used to decode the ensemble
    #
    ######################################################

    # Header
    #
    # !!! start bytes + 1 (made for C originally)
    #
    HeaderBegin = [1, 3, 5, 9, 11, 13]
    HeaderList = ["HID", "DID", "BytesEns", "Spare", "DataTypes"]

    # Fix Leader
    FixLeaderList = [
        "FLID",
        "CPU Version",
        "CPU Revision",
        "System Configuration",
        "Real/sim flag",
        "spare",
        "#bm",
        "WN",
        "WP",
        "WS",
        "WF",
        "WM",
        "WC",
        "#cr",
        "WG",
        "WE",
        "TPPmm",
        "TPPss",
        "TPPhh",
        "EX",
        "EA",
        "EB",
        "EZ",
        "EC",
        "dis1",
        "WT",
        "WP/WL",
        "WA",
        "Spare",
        "LagD",
        "CPUserial",
        "WB",
        "CQ",
    ]

    # Byte length of the Fix Leader Data
    FixLeaderBytes = [
        2,
        1,
        1,
        2,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        1,
        1,
        1,
        1,
        2,
        1,
        1,
        1,
        1,
        2,
        2,
        1,
        1,
        2,
        2,
        2,
        1,
        1,
        2,
        8,
        2,
        1,
    ]

    # Variable Leader
    VariableLeaderList = [
        "VLID",
        "ENS",
        "RTCyymmddhhmmsshh",
        "#MSB",
        "BIT",
        "EC",
        "ED",
        "EH",
        "EP",
        "ER",
        "ES",
        "ET",
        "MPTmmsshh stDev",
        "Heading StDev",
        "Pitch StdeV",
        "Roll StDev",
        "ADC ch 0",
        "ADC ch 1",
        "ADC ch 2",
        "ADC ch 3",
        "ADC ch 4",
        "ADC ch 5",
        "ADC ch 6",
        "ADC ch 7",
        "ESW",
        "Res",
        "Pressure",
        "Pressure STD",
        "Spare",
        "RTCccyymmddhhmmsshh",
    ]

    # byte length of the Variable Leader Data
    VariableLeaderBytes = [
        2,
        2,
        7,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        4,
        2,
        4,
        4,
        1,
        8,
    ]

    BottomTrackList = [
        "BTID",
        "BP",
        "BD",
        "BC",
        "BA",
        "BG",
        "BM",
        "BE",
        "Reserved",
        "Beam#1 BT Range",
        "Beam#2 BT Range",
        "Beam#3 BT Range",
        "Beam#4 BT Range",
        "Beam#1 BT Vel",
        "Beam#2 BT Vel",
        "Beam#3 BT Vel",
        "Beam#4 BT Vel",
        "Beam#1 BT Corr",
        "Beam#2 BT Corr",
        "Beam#3 BT Corr",
        "Beam#4 BT Corr",
        "Beam#1 BT Eval Amp",
        "Beam#2 BT Eval Amp",
        "Beam#3 BT Eval Amp",
        "Beam#4 BT Eval Amp",
        "Beam#1 BT %Good",
        "Beam#2 BT %Good",
        "Beam#3 BT %Good",
        "Beam#4 BT %Good",
        "Ref Layer Min (BL)",
        "Ref Layer Near (BL)",
        "Ref Layer Far (BL)",
        "Beam#1 Ref Layer Vel",
        "Beam#2 Ref Layer Vel",
        "Beam#3 Ref Layer Vel",
        "Beam#4 Ref Layer Vel",
        "Beam#1 Ref Corr",
        "Beam#2 Ref Corr",
        "Beam#3 Ref Corr",
        "Beam#4 Ref Corr",
        "Beam#1 Ref Int",
        "Beam#2 Ref Int",
        "Beam#3 Ref Int",
        "Beam#4 Ref Int",
        "Beam#1 Ref %Good",
        "Beam#2 Ref %Good",
        "Beam#3 Ref %Good",
        "Beam#4 Ref %Good",
        "BX",
        "Beam#1 RSSI AMP",
        "Beam#2 RSSI AMP",
        "Beam#3 RSSI AMP",
        "Beam#4 RSSI AMP",
        "Gain",
    ]
    BottomTrackBytes = [
        2,
        2,
        2,
        1,
        1,
        1,
        1,
        2,
        4,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        1,
        1,
        1,
        1,
        1,
    ]

    DataName = {
        "0000": "Fix Leader",
        "8000": "Variable Leader",
        "0001": "Velocity",
        "0002": "Correlation Profile",
        "0003": "Echo Intensity Profile",
        "0004": "Percent Made Good",
        "0005": "Status Profile",
        "0006": "Bottom Track",
    }

    # Data dictionnaries
    Header = {}
    FixLeader = {}
    VariableLeader = {}
    BottomTrack = {}

    Data = {
        "VID": 2,
        "CMID": 2,
        "ECIID": 2,
        "PCGID": 2,
    }

    ######################################################
    # Decoding
    ######################################################

    try:

        ###########################
        # HEADER
        ###########################

        for i in range(len(HeaderBegin) - 1):
            val = Line[HeaderBegin[i] - 1: HeaderBegin[i + 1] - 1]
            if len(val) == 2:
                if i > 1:
                    dval = s16(val)
                else:
                    dval = val
            elif len(val) == 4:
                conv = "%s%s" % (val[2:], val[:2])
                # dval = int(conv, base=16)
                dval = s16(conv)
            Header[HeaderList[i]] = dval

        start = HeaderBegin[-1] - 1
        for i in range(Header["DataTypes"]):
            val = Line[start: start + 4]
            conv = "%s%s" % (val[2:], val[:2])
            # dval = int(conv, base=16)
            dval = s16(conv)
            DataCode = Line[dval * 2: dval * 2 + 4]
            Header[DataName[DataCode]] = dval
            start += 4
        if out:
            print("=======================")
            print("HEADER")
            print("=======================")
            for key, val in Header.items():
                print(key, val)

        ###########################
        # FIX LEADER
        ###########################
        print("Number of bytes in Fix Leader:", sum(np.array(FixLeaderBytes)))

        # position of the first byte of FIX LEADER
        start = Header["Fix Leader"] * 2

        for i in range(len(FixLeaderList)):
            converted_data = None
            val = Line[start: start + FixLeaderBytes[i] * 2]
            if FixLeaderBytes[i] == 1:
                converted_data = s16(val)
            elif FixLeaderBytes[i] == 2:
                if i > 0:
                    converted_data = s16(val[2:] + val[:2])
                else:
                    converted_data = val
            else:
                # decode each byte and assemble a composite value
                converted_data = ""
                for j in range(FixLeaderBytes[i]):
                    converted_data += str(s16(val[j * 2: (j + 1) * 2]))

            FixLeader[FixLeaderList[i]] = converted_data
            if FixLeaderList[i] == "WF":
                Data["Blank"] = converted_data
            if FixLeaderList[i] == "WN":
                Data["NCells"] = converted_data
            if FixLeaderList[i] == "WS":
                Data["CellSize"] = converted_data

            start += FixLeaderBytes[i] * 2

        z = []
        for i in range(int(Data["NCells"])):
            z.append(int(Data["Blank"]) + int(Data["CellSize"]) * (i + 1))
        Data["Depth"] = z

        if out:
            print("=======================")
            print("FIX LEADER")
            print("=======================")
            for key, val in FixLeader.items():
                print(key, val)

        ###########################
        # VARIABLE LEADER DATA
        ###########################
        print("Number of bytes in Variable Leader:",
              sum(np.array(VariableLeaderBytes)))
        # position of the first byte of VARIABLE LEADER
        start = Header["Variable Leader"] * 2

        for i in range(len(VariableLeaderList)):
            val = Line[start: start + VariableLeaderBytes[i] * 2]
            if VariableLeaderBytes[i] == 1:
                # VariableLeader[VariableLeaderList[i]] = int(val, base=16)
                VariableLeader[VariableLeaderList[i]] = s16(val)
            elif VariableLeaderBytes[i] == 2:
                if i > 0:
                    VariableLeader[VariableLeaderList[i]] = s16(
                        val[2:] + val[:2])
                else:  # keep the header code as it is
                    VariableLeader[VariableLeaderList[i]] = val
            else:
                # decode each byte and assemble a composite value
                sval = ""
                # print(val)
                for j in range(VariableLeaderBytes[i]):
                    tmpval = s16(val[j * 2: (j + 1) * 2])
                    if tmpval < 10:
                        sval += "0" + str(tmpval)
                    else:
                        sval += str(tmpval)
                VariableLeader[VariableLeaderList[i]] = sval
            start += VariableLeaderBytes[i] * 2

        if out:
            print("=======================")
            print("VARIABLE LEADER DATA")
            print("=======================")
            for key, val in VariableLeader.items():
                print(key, val)

        ###########################
        # VELOCITY DATA
        ###########################
        # position of the first byte
        start = Header["Velocity"] * 2

        Data["Velocity"] = decode_ADCP_data(
            Line, start, Data["VID"], 2, Data["NCells"])

        ###########################
        # CORRELATION MAGNITUDE
        ###########################
        # position of the first byte
        start = Header["Correlation Profile"] * 2
        Data["CorrelMag"] = decode_ADCP_data(
            Line, start, Data["CMID"], 1, Data["NCells"]
        )

        ###########################
        # ECHO INTENSITY PROFILE
        ###########################
        # position of the first byte of Echo Intensity Profile
        start = Header["Echo Intensity Profile"] * 2

        Data["Echo Intensity"] = decode_ADCP_data(
            Line, start, Data["ECIID"], 1, Data["NCells"]
        )

        ###########################
        # PERCENT MADE GOOD
        ###########################
        # position of the first byte of Percent Made Good
        start = Header["Percent Made Good"] * 2
        Data["Percent Good"] = decode_ADCP_data(
            Line, start, Data["PCGID"], 1, Data["NCells"]
        )

        if out:
            print("=======================")
            print("DATA")
            print("=======================")
            for key, val in Data.items():
                print(key, val)

        ###########################
        # BOTTOM TRACK
        ###########################
        start = Header["Bottom Track"] * 2

        for i in range(len(BottomTrackList)):
            val = Line[start: start + BottomTrackBytes[i] * 2]
            if BottomTrackBytes[i] == 1:
                # BottomTrack[BottomTrackList[i]] = int(val, base=16)
                BottomTrack[BottomTrackList[i]] = s16(val)
            elif BottomTrackBytes[i] == 2:
                if i > 0:
                    BottomTrack[BottomTrackList[i]] = s16(val[2:] + val[:2])
                else:
                    BottomTrack[BottomTrackList[i]] = val
            else:
                sval = ""
                for j in range(BottomTrackBytes[i]):
                    tmpval = s16(val[j * 2: (j + 1) * 2])
                    if tmpval < 10:
                        sval += "0" + str(tmpval)
                    else:
                        sval += str(tmpval)
                BottomTrack[BottomTrackList[i]] = sval

            start += BottomTrackBytes[i] * 2

        if out:
            print("=======================")
            print("BOTTOM TRACK")
            print("=======================")
            for key, val in BottomTrack.items():
                print(key, val)

    except:
        print("!!! Line %i not decoded" % (LN))

    ###########################
    # return dictionnaries
    ###########################
    return Header, FixLeader, VariableLeader, Data, BottomTrack


def decode_ADCP_data(Line, start, id_num_bytes, data_bytes, NCells):
    """Reads Data portion from ADCP ensemble
    Applies to
    * Velocity,
    * Correlation Magnitude,
    * Echo Intensity Profile,
    * Percent Good

    :param Line: str of hexascii bytes, Ensemble to decode
    :param start: int byte position of the start byte
    :param id_num_bytes: int, number of bytes of ID code
    :param data_bytes: int, number of bytes per data value
    :param Ncells: int, number of cells per ensemble

    :returns: decoded data
    :rtype: list
    """
    # read data id and skip it
    val = Line[start: start + id_num_bytes * 2]

    data_list = []
    for i in range(NCells):
        d = []
        for j in range(4):
            val = Line[start: start + data_bytes * 2]
            if data_bytes == 2:
                hex = val[2:] + val[:2]
            else:
                hex = val
            d.append(s16(hex))
            start += data_bytes * 2
        data_list.append(d)
    return data_list


def checksum(Ensemble):
    """Performs checsum of Ensemble

    :param Ensemble: Hex-ascii string to be decoded
    :returns: true if checksum succeeds, False if checksum fails

    """

    Checksum1 = 0
    for i in range(int(len(Ensemble[:-4]) / 2)):
        Checksum1 += int(Ensemble[i * 2: i * 2 + 2], base=16)
    Checksum2 = Ensemble[-2] + Ensemble[-1] + \
        Ensemble[-4] + Ensemble[-3]
    Checksum2 = int(Checksum2, base=16)

    if Checksum1 == Checksum2:
        return True
    else:
        return False


def read_ADCP(t0=0, dirname="./", out=False):
    """reads and ADCP data file and translates the content into readable values

    :param t0: int, common starting time used for filename
    :param dirname: str, data storage directory
    :param out: boolean, print out results if True

    :returns: list of ADCPEnsemble
    :rtype: list
    """

    #
    # variables to read
    #
    BadEnsemble = 0
    Ensemble_list = []

    #
    # filename to read
    # read all in one
    #
    fname = dirname + "ADCP_" + str(t0) + ".txt"

    f = open(fname, "r")
    Lines = f.readlines()

    f.close()

    # line number
    LN = 1
    BadEnsemble = 0
    TotEnsemble = 0
    for Line in Lines:
        if ',' in Line:
            data = Line.split(',')
            Ensemble = data[1]
            if data[1][0:4] == "7F7F":
                TotEnsemble += 1
                # checksum the ensemble
                Ensemble = data[1].strip("\n")
                if checksum(Ensemble):  # if checksum passed decode ensemble
                    h, fl, vl, da, bt = Process_Ensemble(Ensemble, LN, out=out)
                    Ensemble_list.append(ADCPEnsemble(h, fl, vl, da, bt))
                else:
                    BadEnsemble += 1
                    print("Bad checksum")
            LN += 1
    print("Number of ensembles", TotEnsemble)
    print("Number of bad ensembles", BadEnsemble)
    return (Ensemble_list)


def s16(value):
    """Returns signed int from hex

    adapted from
    https://stackoverflow.com/questions/24563786/conversion-from-hex-to-signed-dec-in-python

    :param value: hex string to convert
    :returns: converted signed integer value
    :rtype: int
    """

    value = int(value, base=16)
    return -(value & 0x8000) | (value & 0x7FFF)


def decode_parsed_GPS(sentence):
    """Decodes sentence and returns dic with fields and values

    :param sentence: parsed sentence to recode
    :returns: parsed GPS data dictionnary
    :rtype: dic
    """

    GPS_data_dic = {}
    if sentence != "-1":
        sentence = pynmea2.parse(sentence)
        for field in sentence.fields:
            value = getattr(sentence, field[1])
            GPS_data_dic[field[1]] = value

    return GPS_data_dic


def decode_PA(sentence):
    """Decodes a PA sentence and returns depth and date

    :param sentence: nmea string
    :returns: list of values
    :rtype: list
    """

    try:
        data = sentence.strip("\n").split(",")
        t = data[1]
        for i in range(len(data)):
            if "M" in data[i]:
                z = data[i - 1]
        return [t, z]
    except:
        return [str(datetime.now()), "bad sentence"]


def read_GPS(t0=0, dirname='./', out=True):
    """reads GPS data file extracts GNGGA sentences into a list

    :param t0: int, common starting time used for filename
    :param dirname: str, data storage directory
    :param out: boolean, print out results if True

    :returns: res, list of GPS coordinates and time
    :rtype: list

    """
    fname = dirname + "ADCP_" + str(t0) + ".txt"

    # f = open(fname, "r")
    f = open("/home/metivier/Nextcloud/src/GPS/LibGPS/GPSout.txt", "r")
    Lines = f.readlines()
    f.close()

    res = []
    for line in Lines:
        if line[0:6] == '$GNGGA':
            GPS = decode_parsed_GPS(line.strip('\n'))
            lat = float(GPS["lat"])/100
            if GPS["lat_dir"] == 'S':
                lat *= -1
            lon = float(GPS["lon"])/100
            if GPS["lon_dir"] == 'W':
                lon *= -1
            el = float(GPS["altitude"])
            res.append([GPS["timestamp"], lat, lon, el])
    if out:
        for r in res:
            print(r)

    return res


if __name__ == "__main__":

    ######################################################
    # reads the code of the last acquisition and decodes
    ######################################################

    dirname = "/home/metivier/Nextcloud/src/LibField/Data/"
    with open(dirname+'last_t0.txt') as f:
        t0 = f.readline().strip('\n')

    print(t0)
    ProfList = read_ADCP(t0, dirname, True)
    P0 = ProfList[0]

    print(P0.Data["Velocity"])

    print(P0.VADCP)
    print(P0.VGeo)

    # read_GPS()
