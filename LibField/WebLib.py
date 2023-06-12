from bottle import route, view, run, request, Bottle, abort, redirect
import time
import LibDecode as LD

# import threading
import os


def get_data(DIRNAME):
    fname = DIRNAME + "last_t0.txt"
    f = open(fname, "r")
    t0 = f.readline().strip("\n")

    res = []
    flist = ["ADCP", "GPS", "PA500"]
    for f in flist:
        fname = DIRNAME + f + "_" + t0 + ".txt"
        with open(fname, "r") as df:
            lines = df.readlines()

        if f == "GPS":
            count = -1
            while "GNGGA" not in lines[count]:
                count -= 1
            res.append(lines[count])
        else:
            res.append(lines[-1])

    return res


@route("/FieldPi")
# @view("/home/pi/Documents/LibField/LibField/page.tpl")
@view("/home/metivier/Nextcloud/src/LibField/LibField/page.tpl")
def FieldPi():

    # target data directory
    # DIRNAME = "/home/pi/Documents/Mayotte/Data/"
    DIRNAME = "/home/metivier/Nextcloud/src/LibField/Data/"

    res = get_data(DIRNAME)

    Pval = LD.decode_PA(res[2])
    GPSdic = LD.decode_parsed_GPS(res[1])

    data = res[0].split(',')
    Ensemble = data[1]
    print(data[1][0:4])
    if data[1][0:4] == "7F7F":
        # checksum the ensemble
        print("ok")
        Ensemble = data[1].strip("\n")
        if LD.checksum(Ensemble):  # if checksum passed decode ensemble
            ADCPdic_list = LD.Process_Ensemble(Ensemble)
        else:
            print("Bad checksum")
            ADCPdic_list = [{}, {}, {}, {}, {}]

        ADCPdic = ADCPdic_list[4]
    else:
        ADCPdic = {"bof": "bof"}

    # get style file
    with open("../Styles/basestyle.css", "r") as f:
        css = f.readlines()

    return {"css": css, "ADCP": ADCPdic, "GPS": GPSdic, "PA": Pval}


@route("/FieldPi", method="POST")
def action():
    Start = request.POST.get("Start")
    Stop = request.POST.get("Stop")

    if Start is not None:
        os.system("python3 /home/pi/Documents/LibField/Runscripts/Run_all.pi &")

    if Stop is not None:
        os.system("sudo killall python3 &")

    redirect("/FieldPi")


run(host="0.0.0.0")
