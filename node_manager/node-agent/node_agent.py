from contextlib import closing
import socket
from crypt import methods
from operator import imod
import pymongo
#from aiokafka import AIOKafkaConsumer
import os
import psutil
import json
import zipfile
import shutil
import subprocess
import socket
import asyncio
import threading
import pymongo
import yaml

from flask import Flask, render_template, request, jsonify
from azure.storage.fileshare import ShareFileClient


app = Flask(__name__)


config_file = os.environ.get("NODE_AGENT_HOME") + "/config.yml"
with open("config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

connection_url = "mongodb://" + cfg["mongo"]["address"]
client = pymongo.MongoClient(connection_url)
database_name = cfg["mongo"]["db"]
app_info = client[database_name]

collection_name = cfg["mongo"]["collection"]
collection = app_info[collection_name]

def getSelfIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    self_ip = s.getsockname()[0]
    s.close()
    return self_ip

def startAppDeployment(deployment_info):
    if "isModel" not in deployment_info:
        return
    print("started deployment consumer")
    app_id = deployment_info['app_id']
    app_instance_id = deployment_info['app_instance_id']
    isModel = deployment_info['isModel']

    free_port = find_free_port()
    self_ip = getSelfIp()
    print("here", app_id, app_instance_id, isModel)
    
    
    if isModel == "1":
        getAppZipFromStorage(app_id, "aibucket", app_instance_id, self_ip, free_port)
    else:
        getAppZipFromStorage(app_id, "appbucket", app_instance_id, self_ip, free_port)

    # updateAppConfig(app_instance_id, self_ip, free_port)

    updateNodeDeploymentStatus(
        app_id, app_instance_id, self_ip, free_port, "Success")


def updateAppConfig(app_instance_id, ip, free_port):
    config_directory = os.environ.get("NODE_AGENT_HOME") + "/" + app_instance_id + "/config"

    isExists = os.path.exists(config_directory)

    if not isExists:
        os.makedirs(config_directory)

    app = {}
    app['app_instance_id']=app_instance_id

    print(config_directory)

    with open(config_directory +'/app.json', 'w') as f:
        json.dump(app, f)

    db = {}
    db['DATABASE_URI'] = ip + ':' + str(free_port)

    print("creating db file")
    with open(config_directory + '/db.json','w')as f:
        json.dump(db, f)

    kafka1 = {}
    kafka1['bootstrap_servers']= cfg["kafka"]["servers"]

    with open(config_directory + '/kafka.json','w')as f:
        json.dump(kafka1, f)

    download_blob("deploymentbucket", "platform_sdk.py")

def download_blob(bucket, file_path):
    sdk_file_path = os.environ.get("NODE_AGENT_HOME") + "/" + file_path
    service = ShareFileClient.from_connection_string(conn_str="https://iasprojectaccount.file.core.windows.net/DefaultEndpointsProtocol=https;AccountName=iasprojectaccount;AccountKey=3m7pA/FPcLIe195UhnJ7bZUMueN8FBPBpKUF42lsEP9xk3ZWzM3XpeSh4NWq+cOOitaLmJbU7hJ2UWLdrVL8NQ==;EndpointSuffix=core.windows.net", share_name=bucket, file_path=file_path)
    with open(sdk_file_path, "wb") as file_handle:
        data = service.download_file()
        data.readinto(file_handle)

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@app.route("/node-agent/getNodeStats", methods=["GET"])
def getNodeStats():
    l1, l2, l3 = psutil.getloadavg()
    CPU_use = (l3/os.cpu_count()) * 100
    RAM_use = psutil.virtual_memory()[2]
    to_send = {"CPU": str(CPU_use), "RAM": str(RAM_use), "Status": "1"}
    return to_send

def updateNodeDeploymentStatus(app_id, app_instance_id, ip, port, status):
    app_info = {
        "_appId": app_id,
        "app_instance_id": app_instance_id,
        "ip": ip,
        "port": port,
        "status": status
    }
    collection.insert_one(app_info)

def getAppZipFromStorage(app_id, bucket_name, app_instance_id, self_ip, free_port):
    print(app_id, bucket_name)
    file = "{}.zip".format(app_id)
    print(file)

    zip_file_name = "{}.zip".format(app_id)
    service = ShareFileClient.from_connection_string(
        conn_str="https://iasprojectaccount.file.core.windows.net/DefaultEndpointsProtocol=https;AccountName=iasprojectaccount;AccountKey=3m7pA/FPcLIe195UhnJ7bZUMueN8FBPBpKUF42lsEP9xk3ZWzM3XpeSh4NWq+cOOitaLmJbU7hJ2UWLdrVL8NQ==;EndpointSuffix=core.windows.net", share_name="appbucket", file_path=file)
    with open(file, "wb") as file_handle:
        data = service.download_file()
        data.readinto(file_handle)
    unzip_run_app(zip_file_name, app_id, app_instance_id, self_ip, free_port)


def unzip_run_app(app_zip_file, app_id, app_instance_id, self_ip, free_port):
    app_zip_full_path = os.environ.get("NODE_AGENT_HOME") + "/" + app_zip_file
    print(app_zip_full_path)

    dest_path = os.environ.get("NODE_AGENT_HOME") + "/" + app_instance_id
    with zipfile.ZipFile(app_zip_full_path, "r") as zipobj:
        zipobj.extractall(dest_path)

    dest_path_after_rename = os.environ.get("NODE_AGENT_HOME") + "/" + app_instance_id
    # os.rename(dest_path, dest_path_after_rename)
    #os.system("mv " + dest_path + " " + dest_path_after_rename)

    updateAppConfig(app_instance_id, self_ip, free_port)

    # try:
    req_file_path = dest_path_after_rename + "/requirements.txt"
        # req_installation_data = subprocess.Popen(
        #     ['pip', 'install', '-r', req_file_path], stdout=subprocess.PIPE)
        # req_installation_output = req_installation_data.communicate()

        # os.system("pip install -r " +  req_file_path)
        # os.chdir(app_instance_id)
        # os.system("python3 " + dest_path_after_rename + "/app.py &")

        # os.chdir('config')

        # data = json.load('config/control.json')
        # for i in data['scripts']:
        #     os.system("python3" + i['filename'] + " " + i['args'] + "&")
    os.chdir(dest_path_after_rename)
    # os.system("pip freeze > requirements.txt")
    print(os.getcwd())
    os.system("sudo docker build -t sample_app:latest .")
    print(free_port)
    os.system("sudo docker run --rm -p 6015:6015 sample_app")
    # print(docker_run_command)
    #docker_run_command = "sudo docker run --rm -p " + str(free_port)  + ":" + str(6015) + " " + app_instance_id + " " + str(free_port)
    # os.system(docker_run_command)
        # os.chdir(os.environ.get("NODE_AGENT_HOME"))
    # except:
    #     print("Requirements not available")


if __name__ == "__main__":
    app.run(port=5001)