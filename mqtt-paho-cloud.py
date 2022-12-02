# Following tutorial https://thenewstack.io/python-mqtt-tutorial-store-iot-metrics-with-influxdb/
# Integrating code from 1_consumer.py and 2_influxDB_simple_Query.py
# if want to collect data more frequently from cloud -> In data explorer of Influx DB -> go to script editor -> change every: 1s to every: 1ms

# Line 6-9 imports the library of InfluxDB database we will use 
import json
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
# Line 10 import the library of MQTT 
import paho.mqtt.client as mqtt
import pandas as pd

from queue import Queue # First come, first out
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


# Personel account
token = 'BUHBJvtOwVYIFy4HZLRdufBLtQ3Gijjtv4pnunqqEi-lxztp2RpbMs1dw2IqQQ4mNRrDU4RAnq0sqS4FxIVDGg=='
org = "sunwellup@gmail.com"
url = "https://ap-southeast-2-1.aws.cloud2.influxdata.com"

# Line 26 creating the object of cloud database by using the above parameters
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org, verify_ssl=False)
# Line 28: The bucket name in the database to store the data in cloud database
_bucket="system"
# Line 30: The API to store data to the cloud database
write_api = client.write_api(write_options=SYNCHRONOUS)

q = Queue();

# ---------------------
# =======  MQTT =======
# ---------------------

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client connects to the broker."""
    print("Connected with result code " + str(rc) + ' by' + str(mqttc._client_id))
    client.subscribe(MQTT_PUBLISH_TOPIC);
    

def on_message(client, userdata, msg):
    """ The callback for when a PUBLISH message is received from the server."""
	# Line 50-58: Store the data to the cloud database, and now they are commented for convenience.
    # InfluxDB logic  (The field key should be the strain/temperature measurement, 
    # and the tag value should be the sensor number) 
    # write the data into influxDB database
    q.put(msg);
    topic_str = str(msg.topic);
    _field, _sensor_id = topic_str.split('/')
    # Convert the payload form JSON into python format
    py_payload = json.loads(msg.payload)
    # Data point with x, y and z directions.(also add timestamp mannually)
    '''
    point = [Point("measurement1").tag("sensor_id", _sensor_id).tag("direction",'x').field(_field, py_payload['acc_x']),
                Point("measurement1").tag("sensor_id", _sensor_id).tag("direction",'y').field(_field, py_payload['acc_y']),
                Point("measurement1").tag("sensor_id", _sensor_id).tag("direction",'z').field(_field, py_payload['acc_z'])]
    # write_api.write(bucket=_bucket, org=org, record=point)
    '''
    print('the sensor id is ' + _sensor_id +' and the value is '+str(msg.payload))
'''
def on_message(client, userdata, msg):
    """ The callback for when a PUBLISH message is received from the server."""
	# Line 50-58: Store the data to the cloud database, and now they are commented for convenience.
    # InfluxDB logic  (The field key should be the strain/temperature measurement, 
    # and the tag value should be the sensor number) 
    # write the data into influxDB database
    topic_str = str(msg.topic);
    _field, _sensor_id = topic_str.split('/')
    msg_str = msg.payload;
    msg_str = msg_str.decode("utf-8")
    # Write Data point to cloud database InfluxDB
    point = Point("measurement1").tag("sensor_id", _sensor_id).field(_field, msg_str)
    print(msg_str)
    write_api.write(bucket=_bucket, org=org, record=point)
    # print('The strain info is ' + msg_str);
'''

def on_publish(client, userdata, mid):
    print('The message has been published')

# MQTT broker config
'''
Available 
'''
MQTT_BROKER_URL = "mqtt.eclipseprojects.io"		# The URL of MQTT broker we will use (This is a cloud MQTT broker)
MQTT_PUBLISH_TOPIC = "acceleration/sensor1"			# The 'Topic' for publishing the data (sensor data)
# MQTT_PUBLISH_TOPIC = "Strain/sensor1"

# MQTT logic - Register callbacks and start MQTT client
mqttc = mqtt.Client(client_id='246428762739', clean_session=False);		# Create an MQTT object 'mqttc' 
# Assign the above three callback functions to the 'mqttc client'
mqttc.on_connect = on_connect; 
mqttc.on_message = on_message;
mqttc.on_publish = on_publish;

mqttc.connect(MQTT_BROKER_URL, port=1883)					# Connect to the MQTT broker



# mqttc.loop_forever()				            # Start a loop for mqtt

mqttc.loop_start();
mqttc.subscribe(topic = MQTT_PUBLISH_TOPIC)		# Subscribe the topic
k = 0;
while True:
    # Get the data from queue and write it into InfluxDB
    if not q.empty():
        data_msg = q.get();
        topic_str = str(data_msg.topic);
        _field, _sensor_id = topic_str.split('/')
        # Convert the payload form JSON into python format
        py_payload = json.loads(data_msg.payload)
        point = [Point("measurement1").tag("sensor_id", _sensor_id).tag("direction",'x').field(_field, py_payload['acc_x']),
                Point("measurement1").tag("sensor_id", _sensor_id).tag("direction",'y').field(_field, py_payload['acc_y']),
                Point("measurement1").tag("sensor_id", _sensor_id).tag("direction",'z').field(_field, py_payload['acc_z'])]
        write_api.write(bucket=_bucket, org=org, record=point);
        # ('the sensor id is ' + _sensor_id +' and the value is '+str(data_msg.payload))
        k = k + 1;













