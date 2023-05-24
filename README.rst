****************
LibField library
****************

Introduction <a class="anchor" id="introdcution"></a>
======================================================

LibField is a set of python functions that helps to handle Field instruments.
NMEA or serial messages are read and dumped into a corresponding file for further processing


A present it handles connection with

* a workhorse ADCP
* a PA500 Tritech echosounder
* a GPS (I use ZedFp9 Ardusimple RTK GPS)


LibField comes along with a set of RunScripts to launch data acquisition.

* Run_as_threads.py launches all instrument acquisitions as threads
* Run_one.py is to be used on a command line terminal to laung one instrument
* Run_all.py wraps three Run_one commands using os.system() instruction.


These files can then to be used with a Raspberry pi  to collects data and post logging information on the web.


Requirements and Installation <a class="anchor" id="requirements-and-installation"></a>
=====================================================================

Examples <a class="anchor" id="examples"></a>
=============================================
