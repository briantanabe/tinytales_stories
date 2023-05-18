import re
import requests
import os
import json
import uuid

def download_audio(url, folder, filename):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Audio file downloaded and saved as '{file_path}'")
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

def convert_json(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    nodes = {}
    start_node = None
    for node in data['nodes']:
        node_data = {
            "ending": "yes",
            "decisionPoint": "no",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, node["caption"].strip().lower()))
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
                        next_nodes.append(searchNode['caption'])
        if node_data["ending"] == "no":
            if node_data["decisionPoint"] == "no":
                node_data['next'] = next_nodes[0]
            else:
                node_data['next'] = next_nodes
        if len(options_text) > 0:
            node_data['options'] = options_text
        
        nodes[node['caption']] = node_data
        if node['labels'] and node['labels'][0] == "start":
            start_node = node['caption']
        
    output_data = {'nodes': nodes}
    if start_node:
        output_data['startNode'] = start_node

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)



def save_text_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Text file '{file_path}' saved successfully.")
    except IOError:
        print(f"Error: Unable to save text file '{file_path}'.")


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' created successfully.")
        except OSError:
            print(f"Error: Unable to create folder '{folder_path}'.")

def setup_directory(name):

    input = f"stories/{name}/raw_input.json"
    output = f"stories/{name}/processed_input.json"

    if not os.path.exists(input):
        print("Couldn't find raw_input.json... Try again by creating a folder and adding the arrows.app starter file")
        exit()
    
    if not os.path.exists(output):
        convert_json(input, output)

    folder_names = ["text", "audio", "gentle"]
    for folder_name in folder_names:
        folder_path = os.path.join(f'stories/{name}', folder_name)
        create_folder_if_not_exists(folder_path)

def save_clip(id, text, folder):
    save_text_file(f'stories/{folder}/text/{id}.txt', text)
    download_audio(get_audio_link(sample), f'stories/{story_name}/audio', f'{id}.mp3')



# Setup
# story_name = input("What story are we working on: ")
story_name = "test"
setup_directory(story_name)

# Download clip
# id = "test"
# story_name = "test"
# sample = "Despite bring over 3 inches in length, the tarantula is not large enough to have a measurable gravitational pull on the Sun."
# save_clip(id, sample, story_name)