#librerías
import tensorflow as tf
import numpy as np 
import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt 
import json
import requests
import ftplib
import time
import os
import csv

consulta = requests.get("")
file='csv_file.csv'
global f
header = ['TMax', 'Tmin', 'Hum']
#dobby=[14,9,0.23]

def recolectarData():
	data = consulta.json()
	tminDaily = data["feeds"][0]["field3"]
	tmaxDaily =data["feeds"][0]["field4"]
	humidityDaily =str(int(data["feeds"][0]["field2"])/100)


	return [tmaxDaily, tminDaily, humidityDaily]

def reiniciarCSV():
	if(os.path.exists(file) and os.path.isfile(file)):
		os.remove(file)
		print("file deleted")
	else:
		print("file not found")
	f = open(file, 'w', newline='')
	writer = csv.writer(f)
	writer.writerow(header)
	f.close()

def escribirCSV(dataDaily):
	f = open(file, 'a', newline='')
	writer = csv.writer(f)
	writer.writerow(dataDaily)
	f.close()
	print('He escrito')


while True:

	dia = time.localtime()[2]
	hora = time.localtime()[3]
	minutos = time.localtime()[4]
	segundos = time.localtime()[5]

	print(str(hora)+':'+str(minutos)+':'+str(segundos))
	time.sleep(7)
	if dia==28 and hora==19 and minutos==38 and (segundos >= 0 and segundos <= 10): #el día 1 de cada mes a las 12:05
		#volcar dataset
		print("Empezamos a reentrenar")
		dataset= np.genfromtxt('csv_file.csv', delimiter= ',', skip_header = True,usecols=[0,1,2])
		print(dataset)

		#descargar modelo
		print("descargando modelo")
		path = '/'
		filename = 'weather_TxHum.h5'
		ftp = ftplib.FTP("") 
		ftp.login("", "") 
		print("Probando")
		ftp.cwd(path)
		ftp.retrbinary("RETR " + filename, open(filename, 'wb').write)
		ftp.quit()

		#reentrenar modelo a partir de los datos recolectados durante todo el mes
		model = tf.keras.models.load_model('weather_TxHum.h5')
		######model.summary()
		learn_rate = 0.1
		epoch = 200
		model.compile(loss='mse',optimizer='rmsprop',metrics=['mse'])
		model.fit(x = dataset[:,[1,2]], y =dataset[:,0] , epochs=epoch, verbose=0)
		print('dia 27')

		#generar el .tflite
		TF_LITE_MODEL_FILE_NAME = "weather_TxHum.tflite"
		tf_lite_converter = tf.lite.TFLiteConverter.from_keras_model(model)
		tflite_model = tf_lite_converter.convert()
		tflite_model_name = TF_LITE_MODEL_FILE_NAME
		open(tflite_model_name, "wb").write(tflite_model)

		#reiniciar dataset y .csv
		reiniciarCSV()
		#subir el modelo .h5 y .tflite
		filename1 = 'weather_TxHum.h5'
		filename2= 'weather_TxHum.tflite'
		ftp = ftplib.FTP("localhost") 
		ftp.login("", "")
		ftp.storbinary("STOR " + filename1, open(filename1, 'rb'))
		ftp.storbinary("STOR " + filename2, open(filename2, 'rb'))
		ftp.quit()


	if hora==16 and minutos==56 and (segundos >= 0 and segundos <= 6): #cada día a las 23:05
		#recolectar datos de Thingspeak
		print('voy a recolectar datos')
		data = consulta.json()
		tminDaily = data["feeds"][0]["field1"]
		tmaxDaily =data["feeds"][0]["field2"]
		humidityDaily =str(int(data["feeds"][0]["field3"])/100)

		dataDaily = [tmaxDaily, tminDaily, humidityDaily]
		print(dataDaily)

		#escribir en el .csv
		print('voy a escribir')
		escribirCSV(dataDaily)

