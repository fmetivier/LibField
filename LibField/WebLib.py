from bottle import route, view, run, request, Bottle, abort, redirect
import time

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
            res.append(lines[-1])

    return res


@route("/FieldPi")
@view("page.tpl")
def FieldPi():

    # target data directory
    # DIRNAME = "/home/pi/Documents/Mayotte/Data/"
    DIRNAME = "/home/metivier/Nextcloud/src/LibField/Data/"
    res = get_data(DIRNAME)

    return {"ADCP": res[0], "GPS": res[1], "PA": res[2]}


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
