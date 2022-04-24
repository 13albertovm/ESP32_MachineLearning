# Load necessary libraries
## Thingspeak - DHT11
import machine
import network
import ftplib
#import wifi_credentials
from umqtt.simple import MQTTClient
import dht
import time
## oled
from machine import Pin, SoftI2C
import ssd1306
from time import sleep
import ntptime 
#ftp

##microlite
import microlite
import io

# **************************************#
# Objects:
d = dht.DHT11(machine.Pin(14))
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))

# **************************************#
# Configure the ESP32 wifi as STAtion.
ssid = ''  #Nombre de la Red
password = '' #Contraseña de la red
wlan = network.WLAN(network.STA_IF)

print("Empezando")

wlan.active(True)
wlan.connect(ssid, password)

while wlan.isconnected() == False:
  pass

print('Conexion con el WiFi %s establecida' % ssid)
print(wlan.ifconfig()) #Muestra la IP y otros datos del Wi-Fi

# **************************************#
# Global variables and constants:
SERVER = "mqtt.thingspeak.com"
client = MQTTClient("umqtt_client", SERVER)
CHANNEL_ID = ""
WRITE_API_KEY = ""
# topic = "channels/1249898/publish/PJX6E1D8XLV18Z87"
topic = "channels/" + CHANNEL_ID + "/publish/" + WRITE_API_KEY
topic2="channels/1638902/publish/SLVWHRE0VZ29FUJB"
#1000s = 1s
UPDATE_TIME_INTERVAL = 600000 # in ms unit
last_update = time.ticks_ms()
ntptime.host = "1.europe.pool.ntp.org"
#declaracion variables
t=0
h=0
tmin=100
tmax=0
humtmin=75
global prediccion
prediccion=99
refresh=0
#pantalla oled
oled_width = 128
oled_height = 32
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

#ftp
path = '/'
filename = 'weather_TxHum.tflite'

#microlite
hello_world_model = bytearray(2488)
global model_file 

# ***************funciones en prueba***********************#


# **************Funciones***************#
#refrescar pantalla
def refrescar():
    
    oled.fill(0)
    oled.show()
    if minutos<10:
        minutos0 = '0'+str(minutos)
    else:
        minutos0=str(minutos)
    if refresh == 1:
        oled.text('T:'+str(t)+'C || Min:'+str(tmin)+'C', 0, 0)
        oled.text('H:'+str(h)+'% || Max:'+str(tmax)+'C', 0, 10)
        oled.text(str(hora)+':'+minutos0 + ' || Prd:' + str(prediccion)+'C', 0, 20)
    else:
        oled.text('Arrancando', 0, 0)
        oled.text(str((UPDATE_TIME_INTERVAL - (time.ticks_ms() - last_update))/(1000*60))+' min para medir', 0, 10)
        oled.text('Hora local:'+str(hora)+':'+minutos0, 0, 20)
    oled.show()

#microlite
def input_callback (microlite_interpreter):

    global current_input

    inputTensor = microlite_interpreter.getInputTensor(0)

    # print (inputTensor)    
    # print ("position %f" % position)

    x = tmin
    x2=humtmin/100
    # print ("x: %f, " % x)

    x_quantized = float(x)
    x2_quantized = float(x2)

    inputTensor.setValue(0, x_quantized)
    inputTensor.setValue(1, x2_quantized)
    

def output_callback (microlite_interpreter):
    global current_input
    global maxpred
    # print ("output callback")

    outputTensor = microlite_interpreter.getOutputTensor(0)

    # print (outputTensor)

    y_quantized = outputTensor.getValue(0)

    y = y_quantized
    
    maxpred=round(y)
    print ("\n\n\n\n\nPREDICCION: %f" % (y))

# Main loop:
ntptime.settime()
#print('Empieza el LOOP')
#print("Hora de inicio--> "+ str(time.localtime()[3]) + ":"+str(time.localtime()[4]) + ":"+str(time.localtime()[5]))

oled.text('Arrancando', 0, 0)

while True:
    #d.measure()
    
    #líneas en prueba
    gc.collect()
    #wdt_feed()
    #fin de líneas en prueba
    
    dia = time.localtime()[2]
    hora = time.localtime()[3]+2
    if hora==24:
        hora=0
    minutos = time.localtime()[4]
    segundos = time.localtime()[5]    
    refrescar()
    time.sleep(7)
    
    ## Realizamos la predicción del día
    if hora==9 and minutos == 5 and (segundos >= 0 and segundos <= 10): #una vez al día
        time.sleep(3)
        d.measure()
        t = d.temperature()
        h = d.humidity()
        
        #################
        ##Cargar Modelo##
        #################
        if dia == 13:
            ftp = ftplib.FTP("192.168.0.23")
            ftp.login("alberto", "")
            ftp.cwd(path)
            f=open(filename, 'wb')
            #ftp.retrbinary("RETR " + filename, open(filename, 'wb').write)
            ftp.retrbinary("RETR " + filename, f.write)
            f.close()
            ftp.quit()
        model_file= io.open('weather_TxHum.tflite', 'rb')
        ##############
        ##Predicción##
        ##############
        model_file.readinto(hello_world_model)
        model_file.close()
        interp = microlite.interpreter(hello_world_model,2048, input_callback, output_callback)
        interp.invoke()
        prediccion=maxpred
        
        #payload = "field1=" + str(t) + "&field2=" + str(h)
        #payload = "field1={}&field2={}&field3={}&field4={}" .format(str(t), str(h),str(tmin),str(tmax))
        payload = "field5={}" .format(str(prediccion))
        client.connect()
        client.publish(topic, payload)
        client.disconnect()
    #### Enviamos la máxima y mínima al final del día y reiniciamos
    if hora==23 and minutos == 59 and (segundos >= 0 and segundos <= 10): #una vez al día
        time.sleep(3)
        #payload = "field1=" + str(t) + "&field2=" + str(h)
        #payload = "field1={}&field2={}&field3={}&field4={}" .format(str(t), str(h),str(tmin),str(tmax))
        payload = "field3={}&field4={}" .format(str(tmin),str(tmax))
        print("24h: "+payload)
        
        client.connect()
        client.publish(topic, payload)
        client.disconnect()
        
        time.sleep(3)
        d.measure()
        t = d.temperature()
        h = d.humidity()
        tmin = t
        tmax = t
        humtmin = d.humidity()
        
    if time.ticks_ms() - last_update >= UPDATE_TIME_INTERVAL: #cada 10 min 
        refresh = 1
        d.measure()
        t = d.temperature()
        h = d.humidity()
        
        #mostrar actualizacion en la pantalla
        refrescar()
        
        if t > tmax:
            tmax = t
        if t <= tmin:
            tmin = t
            humtmin=h
            
        payload = "field1={}&field2={}&field3={}" .format(str(tmin), str(tmax), str(humtmin))
        client.connect()
        client.publish(topic2, payload)
        client.disconnect()
        
        
        payload = "field1={}&field2={}" .format(str(t), str(h))

        client.connect()
        client.publish(topic, payload)
        client.disconnect()
        print(payload)
        last_update = time.ticks_ms()
        time.sleep(2)
        
        if hora==0 and tmax!=99:
            payload = "field3={}&field4={}" .format(str(tmin),str(tmax))
            print("24h: "+payload)
            client.connect()
            client.publish(topic, payload)
            client.disconnect()
        
