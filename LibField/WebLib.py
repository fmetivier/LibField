from bottle import route, run, template, request, Bottle, abort
import time
import threading

# global variables
ADCP_counter = 0
GPS_counter = 0
PA_counter = 0


def inter_counters():
    global ADCP_counter
    global GPS_counter
    global PA_counter

    while 1:
        ADCP_counter += 10
        GPS_counter += 2
        PA_counter += 1
        time.sleep(0.5)


@route("/FieldPi")
def FieldPi():
    global ADCP_counter
    global GPS_counter
    global PA_counter
    page = """<html>
    </header>
    <meta http-equiv="refresh" content="2">
    </header>
    <body>
    <h3>Data acquired</h3>
    <p>
    <ul>
    <li> ADCP counter: %i
    <li> GPS Counter: %i
    <li> PA Counter: %i
    </ul>
    </p>
    </body>
    </html>
    """ % (
        ADCP_counter,
        GPS_counter,
        PA_counter,
    )
    return page


counters = threading.Thread(target=inter_counters, args=(), daemon=True)
counters.start()

run(host="0.0.0.0", port=8080)
