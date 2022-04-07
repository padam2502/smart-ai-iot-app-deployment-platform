from flask import Flask, render_template, request, jsonify

import pymongo
import os
import logging
import shutil
import zipfile
import requests
import yaml
from queue import PriorityQueue

app = Flask(__name__)

config_file = os.environ.get("NODE_MANAGER_HOME") + "/config.yml"
with open("config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

connection_url="mongodb://" + cfg["mongo"]["address"]
client=pymongo.MongoClient(connection_url)

database_name = cfg["mongo"]["db"]
app_info = client[database_name]

node_deployment_metadata = cfg["mongo"]["collection"]
collection=app_info[node_deployment_metadata]

node_stats_queue = PriorityQueue()
node_to_stats_dict = {}


@app.route("/")
def home():
    return "hello flask"

@app.route("/node-manager/getNewNode", methods=["GET"])
def getNodeStats():
    global node_stats_queue
    global node_to_stats_dict

    response = requests.get("http://" + cfg["initialiser"] + "/initialiser/getDeploymentNodes")
    json_output = response.json()
    print(json_output)
    
    
    for obj in json_output["ips"]:
        st = "http://" + obj["ip"] + ":" +  obj["port"] + "/node-agent/getNodeStats"
        print(st) 
        resp = requests.get("http://" + obj["ip"] + ":" + obj["port"] + "/node-agent/getNodeStats")
        output = resp.json()
        node_stats_queue.put(output["CPU"], output["RAM"])
        node_to_stats_dict[obj["ip"]] = [output["CPU"],output["RAM"]]
    

    optimal_node = node_stats_queue.get()

    optimal_ip = ""
    for key, value in node_to_stats_dict.items():
        if  value[0] == optimal_node:
            print("optimal ip found")
            optimal_ip = key
            break

    print(optimal_ip)

    payload = {"ip": optimal_ip}
    return jsonify(payload)
    


@app.route("/node-manager/app/getNode/<app_id>/<app_instance_id>", methods=["GET"])
def appDpeloyedNode(app_id, app_instance_id):
    cursor = collection.find_one({"app_id": app_id, "app_instance_id": app_instance_id})
    for doc in cursor:
        deployed_ip = doc["ip"]
        deployed_port = doc["port"]

    out = {"ip": deployed_ip, "port": deployed_port}

    return jsonify(out)




if __name__ == "__main__":
    app.run(port = 5000)