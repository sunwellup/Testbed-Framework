# Following tutorial https://thenewstack.io/python-mqtt-tutorial-store-iot-metrics-with-influxdb/
# Integrating code from 1_consumer.py and 2_influxDB_simple_Query.py
# if want to collect data more frequently from cloud -> In data explorer of Influx DB -> go to script editor -> change every: 1s to every: 1ms

# Line 6-9 imports the library of InfluxDB database we will use 
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
# Line 10 import the library of MQTT 
import paho.mqtt.client as mqtt
import json

import random
from time import sleep
import urllib3
urllib3.disable_warnings()


# Line 18-20 Set the Parameters for the InfluxDB cloud database (This is already created so no need to change)
# Parameters: (1) Token: to access to the cloud database; 
#				(2) org: The email address for creating the cloud database in InfluxDB
#				(3) url: The url location of the cloud database we use
token = os.environ.get("-aTVy9tCmoP8tcZzQnT8oHp2ws_QtgmouEUmwIHgIG20-iAVPHsEC1cI5-2NvZXBKfdI4WndyZg9F39r2JnzdA==")
org = "ntusyswell@gmail.com"
url = "https://ap-southeast-2-1.aws.cloud2.influxdata.com"

# Line 26 creating the object of cloud database by using the above parameters
client = influxdb_client.InfluxDBClient(url=url, token="-aTVy9tCmoP8tcZzQnT8oHp2ws_QtgmouEUmwIHgIG20-iAVPHsEC1cI5-2NvZXBKfdI4WndyZg9F39r2JnzdA==", org=org, verify_ssl=False)
# Line 28: The bucket name in the database to store the data in cloud database
bucket="system"
# Line 30: The API to store data to the cloud database
write_api = client.write_api(write_options=SYNCHRONOUS)



# ---------------------
# =======  MQTT =======
# ---------------------


def on_connect(client, userdata, flags, rc):
    """ The callback for when the client connects to the broker."""
    print("Connected with result code " + str(rc) + ' by' + str(mqttc._client_id))

def on_message(client, userdata, msg):
    """ The callback for when a PUBLISH message is received from the server."""
    print(msg.topic+" "+str(msg.payload))
	# Line 50-58: Store the data to the cloud database, and now they are commented for convenience.
    # InfluxDB logic  (The field key should be the strain/temperature measurement, 
    # and the tag value should be the sensor number) 
    # For example: topic = "strain + sensor 1" 
    '''
    point = (Point("measurement1")
            .tag("tagname1", "tagvalue1")
            .field(str(msg.topic), str(msg.payload))
                )
    write_api.write(bucket=bucket, org="ntusyswell@gmail.com", record=point)
    '''

def on_publish(client, userdata, mid):
    pass
    # print('The message has been published')

# MQTT broker config
MQTT_BROKER_URL = "test.mosquitto.org"		# The URL of MQTT broker we will use (This is a cloud MQTT broker)
MQTT_PUBLISH_TOPIC = "acceleration/sensor2"			# The 'Topic' for publishing the data (sensor data)

# MQTT logic - Register callbacks and start MQTT client
mqttc = mqtt.Client(client_id='2');		# Create an MQTT object 'mqttc' 
# Assign the above three callback functions to the 'mqttc client'
mqttc.on_connect = on_connect; mqttc.on_message = on_message
mqttc.on_publish = on_publish

mqttc.connect(MQTT_BROKER_URL)	# Connect to the MQTT broker
mqttc.loop_start()				# Start a loop for mqtt
sleep(1)

while True:
    # Create acceleration in the x, y and z directions
    acc_x = random.uniform(-10,35);	
    acc_y = random.uniform(135,170);	
    acc_z = random.uniform(-10,35);	
    print(f"Published new acceleration/sensor2 measurement: {acc_x, acc_y, acc_z}")
    sleep(1)
    acc_msg = json.dumps({'acc_x':str(acc_x), 'acc_y':str(acc_y), 'acc_z':str(acc_z)})
	# Publish the random temperature 'rantemp' with specific topic 'MQTT_PUBLISH_TOPIC'
    mqttc.publish(topic = MQTT_PUBLISH_TOPIC, payload = acc_msg)
    
