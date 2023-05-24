****************
LibField library
****************

Introduction <a class="anchor" id="introdcution"></a>
======================================================

LibField is a set of python functions that helps to handle Field instruments. A present it handles connection with

* a workhorse ADCP
* a PA500 Tritech echosounder
* a GPS (I use ZedFp9 Ardusimple RTK GPS)


NMEA or serial messages are read and dumped into a corresponding file for further processing

If used as main it is programmed to connect to all three instruments using daemon threads.


Requirements and Installation <a class="anchor" id="requirements-and-installation"></a>
=====================================================================

Examples <a class="anchor" id="examples"></a>
=============================================
