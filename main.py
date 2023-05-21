import re
import requests
import os
import json
import uuid
import time
from tqdm import tqdm
import subprocess
import filecmp

def download_audio(url, folder, filename):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        # print(f"Audio file downloaded and saved as '{file_path}'")
    else:
        print("Failed to download audio file")

def get_audio_link(text):
    url = "https://play.ht/api/v2/tts"

    payload = {
        "quality": "premium",
        "output_format": "mp3",
        "speed": 1,
        "sample_rate": 24000,
        "voice": "jordan",
        "text": text
    }
    headers = {
        "accept": "text/event-stream",
        "content-type": "application/json",
        "AUTHORIZATION": "Bearer f8882704c17b4a5f9ccde4a03ac2cee8",
        "X-USER-ID": "RqUFA8xu26Vw2eHcxkaobk6o3j52"
    }
    response = requests.post(url, json=payload, headers=headers)
    pattern = r'"url":"([^"]+)"'  # Regular expression pattern to match the URL
    match = re.search(pattern, response.text.split("event: completed")[1])
    return match.group(1)

def convert_arrow_json(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    nodes = {}
    start_node = None
    for node in data['nodes']:
        node_data = {
            "ending": "yes",
            "decisionPoint": "no",
            "text": node['caption']
        }
        next_nodes = []
        options_text = []
        for rel in data['relationships']:
            if rel['fromId'] == node['id']:
                node_data["ending"] = "no"
                if rel["type"] != "":
                    node_data["decisionPoint"] = "yes"
                    options_text.append(rel["type"])
                for searchNode in data['nodes']:
                    if searchNode["id"] == rel['toId']:
                        next_nodes.append(str(uuid.uuid5(uuid.NAMESPACE_DNS, searchNode["caption"].strip().lower())))
            if rel['toId'] == node['id']:
                for searchNode in data['nodes']:
                    if searchNode["id"] == rel['fromId']:
                        node_data["previous"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, searchNode["caption"].strip().lower()))
        if node_data["ending"] == "no":
            if node_data["decisionPoint"] == "no":
                node_data['next'] = next_nodes[0]
            else:
                node_data['next'] = next_nodes
        if len(options_text) > 0:
            node_data['options'] = options_text
        
        nodes[str(uuid.uuid5(uuid.NAMESPACE_DNS, node["caption"].strip().lower()))] = node_data
        if node['labels'] and node['labels'][0] == "start":
            start_node = str(uuid.uuid5(uuid.NAMESPACE_DNS, node["caption"].strip().lower()))
        
    output_data = {'nodes': nodes}
    if start_node:
        output_data['startNode'] = start_node

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)



def save_text_file(file_path, content):
    if os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        # print(f"Text file '{file_path}' saved successfully.")
    except IOError:
        print(f"Error: Unable to save text file '{file_path}'.")

    return True


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
            # print(f"Folder '{folder_path}' created successfully.")
        except OSError:
            print(f"Error: Unable to create folder '{folder_path}'.")

def pre_process_story(name):

    input = f"stories/{name}/raw_input.json"
    output = f"stories/{name}/processed_input.json"

    if not os.path.exists(input):
        print("Couldn't find raw_input.json... Try again by creating a folder and adding the arrows.app starter file")
        exit()
    
    convert_arrow_json(input, output)

    folder_names = ["text", "audio", "gentle"]
    for folder_name in folder_names:
        folder_path = os.path.join(f'stories/{name}', folder_name)
        create_folder_if_not_exists(folder_path)

def save_segment(id, text, folder):
    new_file = save_text_file(f'stories/{folder}/text/{id}.txt', text)
    if new_file or not os.path.exists(f'stories/{story_name}/audio/{id}.mp3'):
        download_audio(get_audio_link(text), f'stories/{story_name}/audio', f'{id}.mp3')

    if new_file or not os.path.exists(f'stories/{story_name}/gentle/{id}.json'):
        command = ['python', 'gentle/align.py', f'stories/{story_name}/audio/{id}.mp3', f'stories/{story_name}/text/{id}.txt', '-o', f'stories/{story_name}/gentle/{id}.json']
        try:
            subprocess.run(command, check=True)
            # print("Alignment completed successfully.")
        except subprocess.CalledProcessError as e:
            print("Alignment failed with error:", e)

def download_story_components(name):
    story_json = f"stories/{name}/processed_input.json"
    with open(story_json, 'r') as f:
        data = json.load(f)
        
        print("Deleting existing extra files")
        filenames = []
        directories = [{
            "path": "audio",
            "ext": "mp3"
        },
        {
            "path": "gentle",
            "ext": "json"
        },
        {
            "path": "text",
            "ext": "txt"
        }]
        for node in data['nodes']:
            filenames.append(node)
        for directory in directories:
            for filename in os.listdir(f'stories/{name}/{directory["path"]}'):
                if not filename.endswith(directory["ext"]) or filename.split("/")[-1].split(".")[0] not in filenames:
                    file_path = os.path.join(f'stories/{name}/{directory["path"]}', filename)
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")

        print("Downloading story content")
        for node in tqdm(data['nodes']):
            if "options" in data['nodes'][node].keys():
                for option in data['nodes'][node]["options"]:
                    u = str(uuid.uuid5(uuid.NAMESPACE_DNS, option.strip().lower()))
                    save_segment(u, option, name)

            text = data['nodes'][node]["text"]
            save_segment(node, data['nodes'][node]["text"], name)
            

def process_story(name):
    pre_process_story(name)
    download_story_components(name)


# Setup
story_name = input("What story are we working on: ")
# story_name = "test"
process_story(story_name)