from kafka import KafkaProducer
from matplotlib.pyplot import close
from utils import json_config_loader, get_hash
import json
import threading
from random import randint
import time
import base64
import glob
import random


class SENSOR(threading.Thread):
    def __init__(self, ip_port, sleep_time=5):
        threading.Thread.__init__(self)
        self.ip_port = ip_port
        self.topic = get_hash(self.ip_port)
        self.sleep_time = sleep_time
        self.set_producer()
        self._stopevent = threading.Event()

    def set_producer(self):
        self.producer = KafkaProducer(
            bootstrap_servers=json_config_loader('config/kafka.json')['bootstrap_servers'], value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    def get_data(self):
        pass

    def emit(self):
        self.producer.send(self.topic, self.get_data())

    def flush(self, timeout=None):
        self.producer.flush(timeout=timeout)

    def timeout(self):
        time.sleep(self.sleep_time)

    def close(self):
        if self.producer:
            self.producer.close()

    def run(self):
        try:
            while not self._stopevent.isSet():
                self.emit()
                self.timeout()
            self.producer.flush()
        finally:
            self.close()

    def stop(self):
        self._stopevent.set()

    # def join(self, timeout=None):
    #     """ Stop the thread. """
    #     self.close()
    #     self._stopevent.set()
    #     threading.Thread.join(self, timeout)


class TEMP(SENSOR):
    def get_data(self):
        data = randint(1, 1000)
        print(data)
        return {"data": data}


class PRESSURE(SENSOR):
    def get_data(self):
        data = randint(1, 500)
        print(data)
        return {"data": data}


class IMAGE(SENSOR):
    def set_data_source(self, folder):
        self.img_folder = folder

    def get_data(self):
        image_list = glob.glob(f"{self.img_folder}/*.*")
        img_loc = random.choice(image_list)
        print(f'sending: {img_loc}')
        with open(img_loc, "rb") as image_file:
            image = base64.b64encode(image_file.read())
            image_string = image.decode('utf-8')
            return {"data": image_string}
