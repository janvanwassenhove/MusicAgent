'''
This file contains the GPTAgent class that interacts with the OpenAI API to generate song lyrics.
'''

from openai import OpenAI
import json
import os
from songCreationData import SongCreationData
import requests
import imghdr
class GPTAgent:
    def __init__(self, selected_model, logger, song):
        self.selected_model = selected_model
        self.song_creation_data = SongCreationData(logger)
        self.stop_review_and_modify = False
        self.logger = logger
        self.song = song

    def get_api_key(self):
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
    def get_assistant_content(self, role_name, artist_config):
        for assistant in artist_config["assistants"]:
            if role_name in assistant:
                return assistant[role_name][0]  # Assuming single item in each role's array
        return None

    def execute_phase(self, client, phase, song_creation_data, artist_config, phase_config):
        print("\nExecuting phase ["+phase+"]")

        task_type = ''
        if phase in phase_config:
            task_type = phase_config[phase]["type"]
        else:
            self.logger.info(f"No configuration type for phase: {phase}")

        self.logger.info("\n\nExecuting phase ["+phase+"] (type: " + task_type + ")")

        if task_type == "chat":
            self.discussion(client, phase, song_creation_data, artist_config, phase_config)
        elif task_type == "art":
            album_cover_style = artist_config.get('artist_style')
            image_prompt = "Album cover style defined as: " + album_cover_style + " / Song on the album described as " + self.song_creation_data.song_description
            self.generate_and_download_image(image_prompt, self.song.name, self.song.get_song_dir())
        elif task_type == "readme":
            self.song.create_readme_file(self.song_creation_data)
        elif task_type == "file":
            self.song.create_song_file(self.song_creation_data)
        else:
            return "Unknown task type"

    def discussion(self, client, phase, song_creation_data, artist_config, phase_config):
        if phase in phase_config:
            assistant_role_name = phase_config[phase]["assistant_role_name"]
            user_role_name = phase_config[phase]["user_role_name"]
            phase_prompt = phase_config[phase]["phase_prompt"]
            phase_prompt_str = ''.join(phase_prompt)
        else:
            self.logger.info(f"No configuration found for phase: {phase}")

        assistant_content = self.get_assistant_content(assistant_role_name, artist_config)
        for key, value in phase_config[phase]["input"].items():
            param_value = song_creation_data.get_parameter(value)
            if param_value is not None:
                phase_prompt_str = phase_prompt_str.replace(f"{{{key}}}", str(param_value))

        self.logger.info(
            "\nAssistant is " + assistant_role_name + ", questioned by " + user_role_name + ". \nPrompting:\n " + phase_prompt_str + "\n")

        retry_count = 0
        max_retries = 3  # Adjust this number as needed

        while retry_count < max_retries:
            try:
                # in a next phase, replace chat by assistants
                # assistant = client.beta.assistants.create(
                #     name="Data visualizer",
                #     description=assistant_content,
                #     model=self.selected_model,
                #     tools=[{"type": "code_interpreter"}],
                # )

                # Compose the call to OpenAI
                completion = client.chat.completions.create(
                    model=self.selected_model,  # Replace with your desired model
                    messages=[
                        {"role": "system", "content": assistant_content},
                        {"role": "user", "content": phase_prompt_str}
                    ]
                )
                response_text = completion.choices[0].message.content
                self.logger.info("Response (retry "+str(retry_count)+"): " + response_text)

                # response_text = completion.choices[0].message.content
                # script_start = response_text.find('```ruby') + len('```ruby\n')
                # script_end = response_text.find('```', script_start)
                # sonic_pi_script = response_text[script_start:script_end].strip()

                response_data = json.loads(response_text)

                if "no further code changes are required" in str(response_data):
                    self.logger.info(
                        "Conclusion of review: No further code changes are required. We keep the code like:\n" + self.song_creation_data.sonicpi_code)
                    self.stop_review_and_modify = True
                elif 'sonicpi_code' in response_data and isinstance(response_data['sonicpi_code'], list):
                    # Handle the case where sonicpi_code is a list
                    code_to_retrieve = '\n'.join(response_data['sonicpi_code'])
                    self.logger.info("Code successfully retrieved from array: %s", code_to_retrieve)
                    song_creation_data.set_parameter("sonicpi_code", code_to_retrieve)
                else:
                    song_creation_data.update_parameters_from_response(response_data)
                break
            except json.JSONDecodeError as e:
                self.logger.info(f"Failed to parse the response as JSON: {e}")
                retry_count += 1

                if retry_count >= max_retries:
                    marker = '"sonicpi_code": "'
                    start = response_text.find(marker)
                    if start != -1:
                        start += len(marker)
                        end = response_text.find('"', start)
                        if end != -1:
                            code_to_retrieve = response_text[start:end]
                            self.logger.info("Code could be extracted via workaround: %s", code_to_retrieve)
                            song_creation_data.set_parameter("sonicpi_code", code_to_retrieve)
                        else:
                            self.logger.info("End marker not found for 'sonicpi_code'")
                    else:
                        self.logger.info("Start marker not found for 'sonicpi_code'")
        if retry_count >= max_retries:
            self.logger.info("Maximum number of retries reached, unable to parse JSON")

    def execute_composition_chain(self, genre, duration, additional_information):
        with open('AgentConfig/mITyJohn/MusicCreationPhaseConfig.json') as file:
            phase_config = json.load(file)
        with open('AgentConfig/mITyJohn/MusicCreationChainConfig.json') as file:
            compose_chain_config = json.load(file)
        with open('AgentConfig/mITyJohn/ArtistConfig.json') as file:
            artist_config = json.load(file)

        client = OpenAI()
        client.api_key = self.get_api_key()

        song_description = f"I want to compose a brand new song. I like the "+genre+" genre. If I would describe the song, I would say: "+additional_information

        self.song_creation_data.set_parameter("song_description", song_description)
        self.song_creation_data.set_parameter("total_duration", str(duration))

        # Iterate over phases
        for phase_info in compose_chain_config["chain"]:
            phase = phase_info["phase"]
            if phase_info["phaseType"] == "ComposedPhase":
                # Iterating through cycles
                for cycle_num in range(phase_info["cycleNum"]):
                    if self.stop_review_and_modify :
                        break
                    self.logger.info(f"Executing cycle {cycle_num + 1} of {phase_info['cycleNum']} for ComposedPhase: {phase}; Boolean stop_review_and_modify " + str(self.stop_review_and_modify) )
                    for sub_phase_info in phase_info["Composition"]:
                        sub_phase = sub_phase_info["phase"]
                        if self.stop_review_and_modify :
                            self.logger.info("Skip " + sub_phase);
                            break
                        else:
                            self.logger.info("Starting subphase " + sub_phase);
                            self.execute_phase(client, sub_phase, self.song_creation_data, artist_config, phase_config)
            else:
                self.execute_phase(client, phase, self.song_creation_data, artist_config, phase_config)

    def generate_and_download_image(self, prompt, filename, songdir):
        client = OpenAI()
        client.api_key = self.get_api_key()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
        )

        # Extract image URL from response
        image_url = response.data[0].url
        self.logger.info("image " + image_url)

        # Ensure the directory exists
        if not os.path.exists(songdir):
            os.makedirs(songdir)

        # Download the image
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Detect image type
            image_type = imghdr.what(None, h=image_response.content)
            if image_type:
                # Append the correct extension if necessary
                if not filename.lower().endswith(f".{image_type}"):
                    filename = f"{filename}.{image_type}"

            # Define the full path for the file
            file_path = os.path.join(songdir, filename)

            # Write the file
            with open(file_path, 'wb') as file:
                file.write(image_response.content)
            self.logger.info(f"Image downloaded as {file_path}")
        else:
            self.logger.info("Failed to download image")


