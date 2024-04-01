

from openai import OpenAI
import json
import os
from songCreationData import SongCreationData

def get_api_key():
    # Try to get the API key from an environment variable
    api_key = os.getenv("OPENAI_API_KEY")

    # If not found, fallback to the config file
    if not api_key:
        try:
            with open('AgentConfig/mITyJohn/ArtistConfig.json', 'r') as config_file:
                config = json.load(config_file)
                api_key = config.get('OPENAI_API_KEY')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading config file: {e}")
            return None

    return api_key

# Function to get assistant content from ArtistConfig
def get_assistant_content(role_name, artist_config):
    for assistant in artist_config["assistants"]:
        if role_name in assistant:
            return assistant[role_name][0]  # Assuming single item in each role's array
    return None

def execute_phase(phase, song_creation_data):
    if phase in phase_config:
        assistant_role_name = phase_config[phase]["assistant_role_name"]
        user_role_name = phase_config[phase]["user_role_name"]
        phase_prompt = phase_config[phase]["phase_prompt"]
        phase_prompt_str = ''.join(phase_prompt)

        # print(f"Assistant Role: {assistant_role_name}")
        # print(f"User Role: {user_role_name}")
        # print(f"Phase Prompt: {phase_prompt}")
    else:
        print(f"No configuration found for phase: {phase}")

    assistant_content = get_assistant_content(assistant_role_name, artist_config)
    for key, value in phase_config[phase]["input"].items():
        param_value = song_creation_data.get_parameter(value)
        if param_value is not None:
            phase_prompt_str = phase_prompt_str.replace(f"{{{key}}}", str(param_value))

    print("\n\nExecuting phase ["+phase+"]")
    print("\nAssistant is " + assistant_role_name +", questioned by " + user_role_name+ ". \nPrompting:\n " + phase_prompt_str + "\n")
    # Compose the call to OpenAI
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Replace with your desired model
        messages=[
            {"role": "system", "content": assistant_content},
            {"role": "user", "content": phase_prompt_str}
        ]
    )
    response_text = completion.choices[0].message.content
    # response_text = response_text.strip()  # Remove leading/trailing whitespace
    # response_text = response_text.replace('\\n', '\\\\n')  # Escape newline characters
    # response_text = response_text.replace('\\', '')  # Remove extraneous backslashes

    print("Response: " + response_text)
    try:
        response_data = json.loads(response_text)
        if "no further code changes are required" in str(response_data):
            print("No further code changes are required.")
        else:
            song_creation_data.update_parameters_from_response(response_data)
    except json.JSONDecodeError as e:
        print(f"Failed to parse the response as JSON: {e}")
        marker = '"sonicpi_code": "'
        start = response_text.find(marker)
        if start != -1:
            start += len(marker)
            end = response_text.find('"', start)
            if end != -1:
                code_to_retrieve = response_text[start:end]
                print("Code could be extracted via workaround:", code_to_retrieve)
                song_creation_data.set_parameter("sonicpi_code", code_to_retrieve)
            else:
                print("End marker not found for 'sonicpi_code'")
        else:
            print("Start marker not found for 'sonicpi_code'")


with open('AgentConfig/mITyJohn/MusicCreationPhaseConfig.json') as file:
    phase_config = json.load(file)
with open('AgentConfig/mITyJohn/MusicCreationChainConfig.json') as file:
    compose_chain_config = json.load(file)
with open('AgentConfig/mITyJohn/ArtistConfig.json') as file:
    artist_config = json.load(file)

client = OpenAI()
client.api_key = get_api_key()
modelname = "gpt-3.5-turbo"

song_description = f"I want a song in style of purple disco machine, describing my feeling on rainy weather."
total_duration=180

song_creation_data = SongCreationData()
song_creation_data.set_parameter("song_description", song_description)
song_creation_data.set_parameter("total_duration", str(total_duration))

# Iterate over phases
for phase_info in compose_chain_config["chain"]:
    phase = phase_info["phase"]
    if phase_info["phaseType"] == "ComposedPhase":
        # Iterating through cycles
        for cycle_num in range(phase_info["cycleNum"]):
            print(f"Executing cycle {cycle_num + 1} of {phase_info['cycleNum']} for ComposedPhase: {phase}")
            for sub_phase_info in phase_info["Composition"]:
                sub_phase = sub_phase_info["phase"]
                execute_phase(sub_phase, song_creation_data)
    else:
        execute_phase(phase, song_creation_data)


