****************
LibField library
****************

Introduction
============

LibField is library composed of a set of python functions that helps to handle Field instruments. NMEA or serial messages are read and dumped into a corresponding file for further processing. This library was intended to be used with a Raspberry pi  to collect data autonomously and post logging information on the web. It can also be used from a laptop.


A present it handles connection with

* a workhorse ADCP from Teledyne RDI
* a PA500 Tritech echosounder
* a GPS (I use ZedFP9 Ardusimple RTK GPS)


LibField comes along with a set of RunScripts to launch data acquisition and a simple bottle website to check, from a phone or a laptop,  data acquisition in real-time via the wifi hotspot of the Rasberry Pi.


Libraries
=========

* Libfield: Functions for Data acquisition and storage
* Libdecode: Functions to decode data stored in text files
* Weblib: bootle web sites that sends back the last data acquired


Runscripts
==========

* Run_as_threads.py launches all instrument acquisitions as threads
* Run_one.py is to be used on a command line terminal to launch one instrument
* Run_all.py wraps three Run_one commands using os.system() instruction.
