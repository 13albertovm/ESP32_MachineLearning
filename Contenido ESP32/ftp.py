import ftplib
import os
from machine import Pin
from dht import DHT11 
import network
import urequests
import ujson
from time import sleep

import esp
esp.osdebug(None)

import gc
gc.collect()

ssid = ''
password = ''

api_key = ''

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())
path = '/'
filename = 'weather_TxHum.tflite'

print('durmiendo')
sleep(2)
#os.remove(filename)

ftp = ftplib.FTP("") 
ftp.login("", "") 
ftp.cwd(path)
f=open(filename, 'wb')
#ftp.retrbinary("RETR " + filename, open(filename, 'wb').write)
ftp.retrbinary("RETR " + filename, f.write)
f.close()
ftp.quit()
