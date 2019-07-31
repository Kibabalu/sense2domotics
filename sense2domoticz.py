#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Sending SenseHat and ESP8266 sensor data to Domoticz server.

The data is coming from two data sources: 1. SenseHat, 2. outside ESP8266
module with particle mass sensor SDS011, temperature sensors BMP180 and
DHT022, pressure sensor BMP180 and humidity sensor DHT022. The data is send to
Domoticz server using the json API.

frank.kirschbaum@me.com
"""

import asyncio
import os
from sense_hat import SenseHat
import sys
import urllib.request
import json

sense = SenseHat()

# prefix for communication with domoticz via its json API
url_json = "http://192.168.42.31:8080/json.htm?type=command&param=udevice&idx="

# global data matrix for the measurements: [ name, Domoticz ID, value ]
data_matrix = [['temp_sh', 78, 0],
               ['humidity_sh', 91, 0],
               ['pressure_sh', 89, 0],
               ['part1_sds011', 55, 0],
               ['part2_sds011', 56, 0],
               ['temp_dht', 77, 0],
               ['humidity_dht', 90, 0],
               ['pressure_bmp', 87, 0],
               ['temp_bmp', 74, 0]]


def write_pid_file():
    """
    Write a PID-file to the path given in parameter dest.

    The name of the PID-file consists of argv[0] + '_' + argv[1] + '_'
    + argv[2] + '_' + ...

    :param:
    :return:
    """
    pid = os.getpid()                   # get the PID

    # constructing the PID file name
    file_name = ''
    for arg in sys.argv:                # adding substrings name and parameters
        file_name += arg + '_'          # argv[0] + '_' + argv[1] + '_' + ...
    file_name = file_name[:-1]          # remove last '_'
    file_name += '.pid'                 # add extension '.pid'

    # writing the PID to the PID file
    pid_file = open(file_name, 'w')     # open PID file
    pid_file.write(str(pid))            # write PID to PID file
    pid_file.close()                    # close PID file


async def collect_data_sensehat(cycle_time):
    """
    Read the sensors from sensehat.

    :param integer cycle_time: cycle time
    :return:
    """
    global data

    while True:
        data_matrix[0][2] = float("{0:.2f}".format(sense.get_temperature()))
        data_matrix[1][2] = float("{0:.2f}".format(sense.get_humidity()))
        data_matrix[2][2] = float("{0:.2f}".format(sense.get_pressure()))

        print("sensor data from SenseHat read")

        await asyncio.sleep(cycle_time)


async def collect_data_ESP8266(cycle_time):
    """
    Collect data from ESP8266 with the sensors SDS011, BMP180 and DHT22.

    :param integer cycle_time: cycle time
    :return:
    """
    global data

    while True:
        try:
            with urllib.request.urlopen("http://192.168.42.39/data.json") as url:
                data = json.loads(url.read().decode())

                part1_sds011 = float(data['sensordatavalues'][0]['value'])
                part2_sds011 = float(data['sensordatavalues'][1]['value'])
                temp_dht = float(data['sensordatavalues'][2]['value'])
                humidity_dht = float(data['sensordatavalues'][3]['value'])
                pressure_bmp = float(data['sensordatavalues'][4]['value'])
                temp_bmp = float(data['sensordatavalues'][5]['value'])

                # Format the data
                data_matrix[3][2] = float("{0:.2f}".format(part1_sds011))
                data_matrix[4][2] = float("{0:.2f}".format(part2_sds011))
                data_matrix[5][2] = float("{0:.2f}".format(temp_dht))
                data_matrix[6][2] = float("{0:.2f}".format(humidity_dht))
                data_matrix[7][2] = float("{0:.2f}".format(pressure_bmp))
                data_matrix[8][2] = float("{0:.2f}".format(temp_bmp))

                print("Sensor data from ESP8266 read")
        except IOError:
            print("collecting sensor data from ESP8266 failed")

        await asyncio.sleep(cycle_time)


async def send_data_domoticz(cycle_time):
    """
    Send data to Domoticz server using the JSON/API.

    :param integer cycle_time: cycle time
    :return:
    """
    global data

    while True:
        try:
            for ii in range(len(data_matrix)):
                cmd = url_json + str(data_matrix[ii][1]) + "&nvalue=0&svalue=" \
                      + str(data_matrix[ii][2])
                hf = urllib.request.urlopen(cmd)
                print(cmd)

            print('data sent to domoticz')
        except IOError:
            print("sending sensor data to Domoticz failed")

        await asyncio.sleep(cycle_time)

if __name__ == '__main__':

    if len(sys.argv) != 2:                  # check number of arguments
        print('wrong number of parameters. Needed is cycle time in seconds')
        sys.exit(0)

    write_pid_file()                        # write PID-file, e.c. for monit

    # scheduler init stuff:
    print('starting the scheduler')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        send_data_domoticz(int(sys.argv[1])),
        collect_data_sensehat(int(sys.argv[1])),
        collect_data_ESP8266(int(sys.argv[1]))))
    loop.close()
