# inputs : ip | port | temp range
from controller import SPRINKLER
from kafka import KafkaConsumer
import sys
from utils import json_config_loader
import json
KAFKA_SERVERS = json_config_loader(
    'config/kafka.json')["bootstrap_servers"]
# if len(sys.argv) != 3:
#     print('Invalid input')
#     exit(0)
IP = sys.argv[1]
PORT = sys.argv[2]
print("-----------------------------------------------------------------------------------------")
print("{}:{} SPRINKLER".format(IP, PORT))
print("-----------------------------------------------------------------------------------------")
listener_topic = "START_{}_{}".format(IP, PORT)
try:
    consumer = KafkaConsumer(
        listener_topic,
        group_id='simulator',
        bootstrap_servers=KAFKA_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    # Sensor start
    for message in consumer:
        break
    consumer.close()
    sprinkler = SPRINKLER(IP, PORT)
    sprinkler.start()
except:
    print()
    print("-----------------------------------------------------------------------------------------")
    print('Shutting down...')
    print("-----------------------------------------------------------------------------------------")
