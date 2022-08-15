# Following tutorial https://thenewstack.io/python-mqtt-tutorial-store-iot-metrics-with-influxdb/
# Integrating code from 1_consumer.py and 2_influxDB_simple_Query.py
# if want to collect data more frequently from cloud -> In data explorer of Influx DB -> go to script editor -> change every: 1s to every: 1ms

import influxdb_client, os, time
# from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt

# load_dotenv() # take environment variables from .env.

# InfluxDB config
import urllib3
urllib3.disable_warnings()

token = os.environ.get("-aTVy9tCmoP8tcZzQnT8oHp2ws_QtgmouEUmwIHgIG20-iAVPHsEC1cI5-2NvZXBKfdI4WndyZg9F39r2JnzdA==")
org = "ntusyswell@gmail.com"
url = "https://ap-southeast-2-1.aws.cloud2.influxdata.com"

client = influxdb_client.InfluxDBClient(url=url, token="-aTVy9tCmoP8tcZzQnT8oHp2ws_QtgmouEUmwIHgIG20-iAVPHsEC1cI5-2NvZXBKfdI4WndyZg9F39r2JnzdA==", org=org, verify_ssl=False)
bucket="system"
write_api = client.write_api(write_options=SYNCHRONOUS)

# TODO

# MQTT broker config
MQTT_BROKER_URL = "mqtt.eclipseprojects.io"
MQTT_PUBLISH_TOPIC = "temperature90"


mqttc = mqtt.Client()
mqttc.connect(MQTT_BROKER_URL)

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client connects to the broker."""
    print("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
    """ The callback for when a PUBLISH message is received from the server."""
    print(msg.topic+" "+str(msg.payload))
## InfluxDB logic    
    point = (Point("measurement1")
            .tag("tagname1", "tagvalue1")
            .field(str(msg.topic), str(msg.payload))
                )
    write_api.write(bucket=bucket, org="ntusyswell@gmail.com", record=point)
#     time.sleep(0.1) # separate points by 1 second

## MQTT logic - Register callbacks and start MQTT client
mqttc.on_connect = on_connect; mqttc.on_message = on_message
# Subscribe to a topic
mqttc.subscribe(topic = MQTT_PUBLISH_TOPIC) #in getting started documentation it is given as client; so modify accordingly.
mqttc.loop_forever()