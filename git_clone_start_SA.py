import os
import docker
from git import Repo
import json
import shutil
REPO_FOLDER = 'deployment'


def json_config_loader(config_file_loc):
    fstream = open(config_file_loc, "r")
    data = json.loads(fstream.read())
    return data


print('[info]: Deleting previous deployment repository')
if os.path.exists(REPO_FOLDER):
    shutil.rmtree(REPO_FOLDER)
os.mkdir(REPO_FOLDER)
credentials = json_config_loader('git_credentials.json')
username = credentials["username"]
password = credentials["password"]
print('[info]: Downloading deployment package...')
remote = f"https://{username}:{password}@github.com/soumodiptab/smart-ai-iot-app-deployment-platform.git"
Repo.clone_from(remote, REPO_FOLDER)
# add deployment branch later on...
print('[info]: Deployment package downloaded...')
os.chdir(REPO_FOLDER)
# --------------------------------------------------
cwd = os.getcwd()
os.environ["REPO_LOCATION"] = cwd
os.chdir("service_agent")


# docker kill $(docker ps -q)
# docker rm $(docker ps -a -q)
# docker rmi $(docker images -q)

os.system("docker kill $(docker ps -q)")
os.system("docker rm $(docker ps -a -q)")
os.system("docker rmi $(docker images -q)")


os.system("python3 service_agent.py & > /dev/null")

node_agent_dir = cwd + "/node_manager/node-agent"
print(node_agent_dir)
os.chdir(node_agent_dir)
os.system("pip install -r requirements.txt")
os.system("python3 node_agent.py & > /dev/null")