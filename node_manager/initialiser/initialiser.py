from crypt import methods
import pymongo
import os
import logging
import shutil
import zipfile
import requests
import yaml
import urllib.request

from flask import Flask, request, jsonify

from bson.objectid import ObjectId


app = Flask(__name__)

with open("./config.yml", "r") as ymlfile:
    cfg = yaml.full_load(ymlfile)


connection_url="mongodb://" + cfg["mongo"]["address"]
client=pymongo.MongoClient(connection_url)

database_name = cfg["mongo"]["db"]
app_info = client[database_name]

collection_name = cfg["mongo"]["collection"]
collection=app_info[collection_name]

@app.route('/initialiser/getDeploymentNodes', methods=['GET'])
def getDeploymentNodes():
    cursor = collection.find({"name": "node-agent"})
    node_agent_addresses = []
    for doc in cursor:
        node_agent_address = {}
        node_agent_address["ip"] = doc['ip']
        node_agent_address["port"] = doc['port']
        node_agent_addresses.append(node_agent_address)
    return jsonify({"ips": node_agent_addresses})

@app.route('/initialiser/getService/<serviceName>', methods=['GET'])
def getServiceAddress(serviceName):
    # print("hello")
    doc = collection.find_one({"name": serviceName})
    ip = doc["ip"]
    port = doc["port"]
    return jsonify({"ip":ip, "port":port})

def getSelfIp():
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    return external_ip

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port=5003)
