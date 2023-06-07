import sys
import numpy as np


def Process_Ensemble(Line, LN, out=False):
    """Decodes an ADCP Ensemble
    - Header, Fix Leader, Variable Leader and Bottom Track are decoded here
    because they have unique series of parameters
    - Velocity, Correlation Intensity, Echo Intensity, Percent made good are decoded using read_data function

    :param Line: hexascii bytes, the ensemble
    :param LN: int, Line number

    """

    #
    # Lists and dics used to decode the ensemble
    #

    # Header
    HeaderBegin = [1, 3, 5, 9, 11, 13]  # start bytes + 1 (made for C originally)
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
    DataHeader = {}
    BottomTrack = {}

    Data = {
        "VID": 2,
        "NCells": Ncells,
        "CellSize": CellSize,
        "CMID": 2,
        "ECIID": 2,
        "PCGID": 2,
    }

    try:

        # print("=======================")
        # print("HEADER")
        # print("=======================")

        for i in range(len(HeaderBegin) - 1):
            val = Line[HeaderBegin[i] - 1 : HeaderBegin[i + 1] - 1]
            if len(val) == 2:
                # dval = int(val, base=16)
                dval = s16(val)
            elif len(val) == 4:
                conv = "%s%s" % (val[2:], val[:2])
                # dval = int(conv, base=16)
                dval = s16(conv)
            Header[HeaderList[i]] = dval

        start = HeaderBegin[-1] - 1
        for i in range(Header["DataTypes"]):
            val = Line[start : start + 4]
            conv = "%s%s" % (val[2:], val[:2])
            # dval = int(conv, base=16)
            dval = s16(conv)
            DataCode = Line[dval * 2 : dval * 2 + 4]
            Header[DataName[DataCode]] = dval
            start += 4
        if out:
            print("=======================")
            print("HEADER")
            print("=======================")
            for key, val in Header.items():
                print(key, val)

        # print("=======================")
        # print("FIX LEADER")
        # print("=======================")
        print("Number of bytes in Fix Leader:", sum(np.array(FixLeaderBytes)))

        # position of the first byte of FIX LEADER
        start = Header["Fix Leader"] * 2

        for i in range(len(FixLeaderList)):
            val = Line[start : start + FixLeaderBytes[i] * 2]
            if FixLeaderBytes[i] == 1:
                # FixLeader[FixLeaderList[i]] = int(val, base=16)
                FixLeader[FixLeaderList[i]] = s16(val)
            elif FixLeaderBytes[i] == 2:
                # FixLeader[FixLeaderList[i]] = int(val[2:] + val[:2], base=16)
                FixLeader[FixLeaderList[i]] = s16(val[2:] + val[:2])
            else:
                # decode each byte and assemble a composite value
                sval = ""
                for j in range(FixLeaderBytes[i]):
                    # sval += str(int(val[j * 2 : (j + 1) * 2], base=16))
                    sval += str(s16(val[j * 2 : (j + 1) * 2]))
                FixLeader[FixLeaderList[i]] = sval

            start += FixLeaderBytes[i] * 2

        if out:
            print("=======================")
            print("FIX LEADER")
            print("=======================")
            for key, val in FixLeader.items():
                print(key, val)

        # print("=======================")
        # print("VARIABLE LEADER DATA")
        # print("=======================")
        print("Number of bytes in Variable Leader:", sum(np.array(VariableLeaderBytes)))
        # position of the first byte of VARIABLE LEADER
        start = Header["Variable Leader"] * 2

        for i in range(len(VariableLeaderList)):
            val = Line[start : start + VariableLeaderBytes[i] * 2]
            if VariableLeaderBytes[i] == 1:
                # VariableLeader[VariableLeaderList[i]] = int(val, base=16)
                VariableLeader[VariableLeaderList[i]] = s16(val)
            elif VariableLeaderBytes[i] == 2:
                if i > 0:
                    # VariableLeader[VariableLeaderList[i]] = int(
                    #     val[2:] + val[:2], base=16
                    # )
                    VariableLeader[VariableLeaderList[i]] = s16(val[2:] + val[:2])
                else:
                    VariableLeader[VariableLeaderList[i]] = val
            else:
                # decode each byte and assemble a composite value
                sval = ""
                for j in range(VariableLeaderBytes[i]):
                    # sval += str(int(val[j * 2 : (j + 1) * 2], base=16))
                    sval += str(s16(val[j * 2 : (j + 1) * 2]))
                VariableLeader[VariableLeaderList[i]] = sval
            start += VariableLeaderBytes[i] * 2

        if out:
            print("=======================")
            print("VARIABLE LEADER DATA")
            print("=======================")
            for key, val in VariableLeader.items():
                print(key, val)

        z = []
        for i in range(Data["NCells"]):
            z.append(+Data["CellSize"] * (i + 1))
        Data["Depth"] = z

        # print("-----------------------")
        # print("VELOCITY DATA")
        # print("-----------------------")
        # position of the first byte
        start = Header["Velocity"] * 2

        Data["Velocity"] = decode_ADCP_data(Line, start, Data["VID"], 2, Ncells)
        # print(start)

        # print("-----------------------")
        # print("CORRELATION MAGNITUDE")
        # print("-----------------------")
        # position of the first byte
        start = Header["Correlation Profile"] * 2
        Data["CorrelMag"] = decode_ADCP_data(Line, start, Data["CMID"], 1, Ncells)

        # print("-----------------------")
        # print("ECHO INTENSITY PROFILE")
        # print("-----------------------")
        # position of the first byte of Echo Intensity Profile
        start = Header["Echo Intensity Profile"] * 2

        Data["Echo Intensity"] = decode_ADCP_data(Line, start, Data["ECIID"], 1, Ncells)

        # print("-----------------------")
        # print("PERCENT MADE GOOD")
        # print("-----------------------")
        # position of the first byte of Percent Made Good
        start = Header["Percent Made Good"] * 2
        Data["Percent Good"] = decode_ADCP_data(Line, start, Data["PCGID"], 1, Ncells)

        if out:
            print("=======================")
            print("DATA")
            print("=======================")
            for key, val in Data.items():
                print(key, val)

        # print("=======================")
        # print("BOTTOM TRACK")
        # print("=======================")
        start = Header["Bottom Track"] * 2

        for i in range(len(BottomTrackList)):
            val = Line[start : start + BottomTrackBytes[i] * 2]
            if BottomTrackBytes[i] == 1:
                # BottomTrack[BottomTrackList[i]] = int(val, base=16)
                BottomTrack[BottomTrackList[i]] = s16(val)
            elif BottomTrackBytes[i] == 2:
                if i > 0:
                    # BottomTrack[BottomTrackList[i]] = int(val[2:] + val[:2], base=16)
                    BottomTrack[BottomTrackList[i]] = s16(val[2:] + val[:2])
                else:
                    BottomTrack[BottomTrackList[i]] = val
            else:
                sval = ""
                for j in range(BottomTrackBytes[i]):
                    # sval += str(int(val[j * 2 : (j + 1) * 2], base=16))
                    sval += str(s16(val[j * 2 : (j + 1) * 2]))
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

    :return: data_list, decoded data
    :rtype: list
    """
    val = Line[start : start + id_num_bytes * 2]
    data_list = []
    for i in range(NCells):
        d = []
        for j in range(4):
            val = Line[start : start + data_bytes * 2]
            if data_bytes == 2:
                hex = val[2:] + val[:2]
            else:
                hex = val
            d.append(s16(hex))
            start += data_bytes * 2
        data_list.append(d)
    return data_list


def read_ADCP(t0=0, dirname="./"):
    """reads and ADCP data file and translates the content into readable values

    :param t0: int, common starting time used for filename
    :param dirname: str, data storage directory

    """

    #
    # variables to read
    #
    BadEnsemble = 0

    #
    # filename to read
    # read all in one
    #
    # fname = "/home/metivier/Nextcloud/src/LibField/Data/sampleBassin.txt"
    fname = dirname + "ADCP_" + str(t0) + ".txt"
    f = open(fname, "r")
    Lines = f.readlines()
    f.close()

    # line number
    LN = 1
    BadEnsemble = 0
    TotEnsemble = 0
    for Line in Lines:
        if Line[0:4] == "7F7F":
            # print(LN)
            TotEnsemble += 1
            # checksum the ensemble
            Line = Line.strip("\n")
            Checksum1 = 0
            for i in range(int(len(Line[:-4]) / 2)):
                Checksum1 += int(Line[i * 2 : i * 2 + 2], base=16)
            Checksum2 = Line[-2] + Line[-1] + Line[-4] + Line[-3]
            Checksum2 = int(Checksum2, base=16)
            if Checksum1 == Checksum2:  # if checksum passed decode ensemble
                # print("Checksum ok:", Checksum1)
                Process_Ensemble(Line, LN, out=True)
            else:
                BadEnsemble += 1
                print("Bad checksum")
        LN += 1
    print("Number of ensembles", TotEnsemble)
    print("Number of bad ensembles", BadEnsemble)
    # print("Ncells:", Ncells)
    # print("CellSize (cm):", CellSize)


def s16(value):
    """returns signed int from hex

    adapted from
    https://stackoverflow.com/questions/24563786/conversion-from-hex-to-signed-dec-in-python

    :param value: hex string to convert
    """
    value = int(value, base=16)
    return -(value & 0x8000) | (value & 0x7FFF)


if __name__ == "__main__":

    dirname = "/home/metivier/Nextcloud/src/LibField/Data/"
    t0 = 1685956508  # 1685719068
    read_ADCP(t0, dirname)

    print(int("8000", base=16))
    print(s16("8000"))
