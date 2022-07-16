# LibGPS library

* [Introduction](##introduction)
* [Requirements and Installation](##requirements-and-installation)
* [Examples](##examples)




## Introduction <a class="anchor" id="introdcution"></a>

LibGPS is a set of python functions that helps to handle gps data.
It provides simples functions to extract waypoints and tracks from gpx data files produced by Garmin or equivalent GPS devices.
It also enables the real time connection to and acquisition from such devices through NMEA protocol.

## Requirements and Installation <a class="anchor" id="requirements-and-installation"></a>

## Examples <a class="anchor" id="examples"></a>
For a complete example including construction of a folium map see samplescripts

### Retrieve waypoints from a gpx file

```python
from LibGPS import *
import pandas as pd

filename = "../Data/c60x.gpx"
df = get_waypoints(filename)
```

### Get real time GPS

Connection to a GPS antenna that can be connected to the USB or serial port of your computer.

```python
from LibGPS import *

port = "/dev/ttyUSB0" # depends on your device
gps = connect_gps(port)

while True:
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

    sleep(1)
```
