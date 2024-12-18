'''
This file contains the GPTAgent class that interacts with the OpenAI or Anthropic API to generate song lyrics.
'''

from openai import OpenAI
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from audiorecorder import AudioRecorder
from songCreationData import SongCreationData
from sonicPi import SonicPi
from pythonosc import udp_client, dispatcher as osc_dispatcher, osc_server

import json
import os
import requests
import imghdr
import re
import threading
import time
import asyncio

class GPTAgent:
    def __init__(self, selected_model, logger, song, agentType, api_provider):
        self.selected_model = selected_model
        self.song_creation_data = SongCreationData(logger)
        self.stop_review_and_modify = False
        self.logger = logger
        self.song = song
        self.agentType = agentType
        self.api_provider = api_provider
        self.input_callback = None

    def get_user_input(self, prompt):
        if self.input_callback:
            return self.input_callback(prompt)
        print("Input callback not set for webapp. Unable to get user input via modal.")
        return input(prompt)

    def get_api_key(self):
        # Try to get the API key from an environment variable
        env_var = "OPENAI_API_KEY" if self.api_provider == 'openai' else "ANTHROPIC_API_KEY"
        api_key = os.getenv(env_var)

        # If not found, fallback to the config file
        if not api_key:
            try:
                with open('AgentConfig/'+self.agentType+'/ArtistConfig.json', 'r') as config_file:
                    config = json.load(config_file)
                    api_key = config.get(env_var)
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
        self.logger.info(f"Executing phase: [{phase}]")

        task_type = ''
        if phase in phase_config:
            task_type = phase_config[phase]["type"]
        else:
            self.logger.info(f"No configuration type for phase: {phase}")

        self.logger.info("\n\nExecuting phase ["+phase+"] (type: " + task_type + ")")

        assistant_role_name = phase_config[phase]["assistant_role_name"]
        user_role_name = phase_config[phase]["user_role_name"]

        if task_type == "chat":
            self.discussion(client, phase, song_creation_data, artist_config, phase_config)
        elif task_type == "art":
            album_cover_style = artist_config.get('artist_style')
            image_prompt = "Album cover style defined as: " + album_cover_style + " / Song on the album described as " + self.song_creation_data.song_description
            self.generate_and_download_image(image_prompt, self.song.name, self.song.get_song_dir(), phase_config, phase)
        elif task_type == "readme":
            self.logger.info(f"[Questioner]({user_role_name}):[[Create a Readme File containing cover, song parameters, lyrics and structure.]]")
            self.song.create_readme_file(self.song_creation_data)
            self.logger.info(f"[Assistant]({assistant_role_name}):[[Readme file created at {self.song.song_dir} .]]")
        elif task_type == "file":
            self.logger.info(f"[Questioner]({user_role_name}):[[Create the Ruby Song File based on song creation data.]]")
            self.song.create_song_file(self.song_creation_data)
            self.logger.info(f"[Assistant]({assistant_role_name}):[[Ruby song file created at {self.song.song_dir} .]]")
        elif task_type == "human_chat":
            self.human_discussion(artist_config, phase_config, phase)
        elif task_type == "recording":
            self.song_recording(artist_config, self.song_creation_data.total_duration)
        else:
            return "Unknown task type"

    def song_recording(self, artist_config,duration=30):
        self.logger.info(f"Starting song recording phase.")
        recorder = AudioRecorder(self.logger, self.song, artist_config)
        recorder.run(duration=duration, specific_device_index=43)  # Adjust device index as needed

    def human_discussion(self, artist_config, phase_config, phase):
        assistant_role_name = phase_config[phase]["assistant_role_name"]
        user_role_name = phase_config[phase]["user_role_name"]

        self.logger.info(f"[Questioner]({user_role_name}):[[Please provide us your remarks on the song]]")
        self.validate_and_execute_code(self.song_creation_data, artist_config, "")
        review_user = self.get_user_input("\nPlease provide us your remarks on the song: ")
        self.logger.info(f"Received user input: {review_user}")
        self.logger.info(f"[Assistant]({assistant_role_name}):[[{review_user}]]")

        if review_user.strip():  # Check if the input is not empty or just whitespace
            self.song_creation_data.set_parameter("review", review_user)
        else:
            self.logger.info("No review provided, 'review' parameter will not be set.")


    def discussion(self, client, phase, song_creation_data, artist_config, phase_config):
        if phase not in phase_config:
            self.logger.info(f"No configuration found for phase: {phase}")
            return

        assistant_role_name = phase_config[phase]["assistant_role_name"]
        user_role_name = phase_config[phase]["user_role_name"]
        phase_prompt = ''.join(phase_config[phase]["phase_prompt"])

        # Replace placeholders in the prompt with actual values
        for key, value in phase_config[phase]["input"].items():
            param_value = song_creation_data.get_parameter(value)
            self.logger.info(f"Parameter for discussion [{key.upper()}]:[{param_value}]")
            if param_value is not None:
                phase_prompt = phase_prompt.replace(f"{{{key}}}", str(param_value))

        self.logger.info(
            f"Assistant is {assistant_role_name}, questioned by {user_role_name}. \nPrompting:\n {phase_prompt}\n"
        )

        messages = [
            {"role": "user", "content": phase_prompt}
        ]

        # Fetch the system message content
        system_content = self.get_assistant_content(assistant_role_name, artist_config)

        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                if self.api_provider == 'openai':
                    openai_messages = [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": phase_prompt}
                    ]

                    completion = client.chat.completions.create(
                        model=self.selected_model,
                        messages=openai_messages
                    )
                    response_text = completion.choices[0].message.content

                elif self.api_provider == 'anthropic':  # Anthropic
                    completion = client.messages.create(
                        model=self.selected_model,
                        system=system_content,  # Use top-level 'system' parameter in case of Anthropic
                        messages=messages,
                        max_tokens=4096,
                    )
                    response_text = completion.content[0].text

#                 self.logger.info(
#                     f"\Assistant is {assistant_role_name}, questioned by {user_role_name}. \nPrompting:\n {phase_prompt}\n"
#                 )
                phase_prompt_single_line = phase_prompt.replace('\n', ' ')
                self.logger.info(f"[Questioner]({user_role_name}):[[{phase_prompt_single_line}]]")
                response_text_single_line = response_text.replace('\n', ' ')
                self.logger.info(f"[Assistant]({assistant_role_name}):[[{response_text_single_line}]]")

                self.logger.info(f"Response (retry {retry_count}): {response_text}")

                # Attempt to extract JSON object using regex if the response contains extra text
                match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if match:
                    response_data = json.loads(match.group(0))
                else:
                    response_data = json.loads(response_text)

                if "no further code changes are required" in str(response_data):
                    self.logger.info(
                        "Conclusion of review: No further code changes are required. We keep the code like:\n"
                        + self.song_creation_data.sonicpi_code
                    )
                    self.stop_review_and_modify = True
                elif 'sonicpi_code' in response_data:
                    if isinstance(response_data['sonicpi_code'], list):
                        code_to_retrieve = '\n'.join(response_data['sonicpi_code'])
                    elif isinstance(response_data['sonicpi_code'], str):
                        code_to_retrieve = response_data['sonicpi_code']
                    self.logger.info(f"Code successfully retrieved: {code_to_retrieve}")
                    song_creation_data.set_parameter("sonicpi_code", code_to_retrieve)
                    self.song.create_song_file(song_creation_data)
                else:
                    song_creation_data.update_parameters_from_response(response_data)

                if phase_config[phase].get("codeValidation", False):
                    if self.validate_and_execute_code(song_creation_data, artist_config, response_text):
                        break
                    self.logger.info(f"Error detected in Sonic Pi code, should be corrected before continuing.")
                    retry_count += 1
                else:
                    break

            except json.JSONDecodeError as e:
                self.logger.info(f"Failed to parse the response as JSON: {e}")
                if self.handle_json_decode_error(response_text, song_creation_data, phase_config[phase], artist_config):
                    break
                retry_count += 1

        if retry_count >= max_retries:
            self.logger.info("Maximum number of retries reached, unable to parse JSON")

    def validate_and_execute_code(self, song_creation_data, artist_config, response_text):
        self.song.create_song_file(song_creation_data)
        self.logger.info(f"Running song in Sonic Pi: {self.song.song_dir}/{self.song.name}")
        feedback_message = self.run_sonic_pi_script(self.song, artist_config)

        if feedback_message is not None and "error" in feedback_message.lower():
            self.logger.info(f"Error detected in Sonic Pi execution: {feedback_message}")
            self.append_feedback_messages(response_text, feedback_message)
            return False
        return True

    def append_feedback_messages(self, response_text, feedback_message):
        self.messages.append({"role": "assistant", "content": response_text})
        self.messages.append({"role": "user", "content": f"Feedback from Sonic Pi: {feedback_message}. Please correct the code."})

    def handle_json_decode_error(self, response_text, song_creation_data, phase_config, artist_config):
        marker = '"sonicpi_code": "'
        start = response_text.find(marker)
        if start != -1:
            start += len(marker)
            end = response_text.find('"', start)
            if end != -1:
                code_to_retrieve = response_text[start:end]
                self.logger.info(f"Code extracted via workaround: {code_to_retrieve}")
                song_creation_data.set_parameter("sonicpi_code", code_to_retrieve)
                self.song.create_song_file(song_creation_data)
            else:
                self.logger.info("End marker not found for 'sonicpi_code'")
        else:
            self.logger.info("Start marker not found for 'sonicpi_code'")
        return False


    def execute_composition_chain(self, genre, duration, additional_information):
        with open('AgentConfig/'+self.agentType+'/MusicCreationPhaseConfig.json') as file:
            phase_config = json.load(file)
        with open('AgentConfig/'+self.agentType+'/MusicCreationChainConfig.json') as file:
            compose_chain_config = json.load(file)
        with open('AgentConfig/'+self.agentType+'/ArtistConfig.json') as file:
            artist_config = json.load(file)

        if self.api_provider == 'openai':
            client = OpenAI(api_key=self.get_api_key())
        else:
            client = Anthropic(api_key=self.get_api_key())

        song_description = f"I want to compose a brand new song. I like the "+genre+" genre. If I would describe the song, I would say: "+additional_information

        self.song_creation_data.set_parameter("song_description", song_description)
        self.song_creation_data.set_parameter("total_duration", str(duration))

        self.logger.info(f"Parameter used [DURATION]:[{duration}], [GENRE]:[{genre}], [DESCRIPTION]:[{additional_information}]")

        # Iterate over phases
        for phase_info in compose_chain_config["chain"]:
            phase = phase_info["phase"]

            if phase_info["phaseType"] == "ComposedPhase":
                # Iterating through cycles
                for cycle_num in range(phase_info["cycleNum"]):
                    if self.stop_review_and_modify:
                        break
                    self.logger.info(f"Executing cycle {cycle_num + 1} of {phase_info['cycleNum']} for ComposedPhase: {phase}; Boolean stop_review_and_modify " + str(self.stop_review_and_modify) )
                    for sub_phase_info in phase_info["Composition"]:
                        sub_phase = sub_phase_info["phase"]
                        if self.stop_review_and_modify:
                            self.logger.info("Skip " + sub_phase)
                            break
                        else:
                            # self.logger.info("Starting subphase " + sub_phase)
                            self.execute_phase(client, sub_phase, self.song_creation_data, artist_config, phase_config)
            else:
                self.execute_phase(client, phase, self.song_creation_data, artist_config, phase_config)

    def generate_and_download_image(self, prompt, filename, songdir, phase_config, phase):
        if self.api_provider == 'openai':
            client = OpenAI(api_key=self.get_api_key())
        else:
            # Anthropic doesn't have an image generation API, so we'll need to use an alternative
            self.logger.info("Image generation not supported with Anthropic API.")
            return

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

        if songdir == "":
            songdir = os.path.join('songs', filename)

        # Ensure the directory exists
        if not os.path.exists(songdir):
            os.makedirs(songdir)

        assistant_role_name = phase_config[phase]["assistant_role_name"]
        user_role_name = phase_config[phase]["user_role_name"]
        self.logger.info(f"[Questioner]({user_role_name}):[[{prompt}]]")
        self.logger.info(f"[Assistant]({assistant_role_name}):[[Cover image generated {image_url} .]]")

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


    def run_sonic_pi_script(self, song, artist_config):
        sonic_pi = SonicPi(self.logger)
        feedback_message  = sonic_pi.call_sonicpi(song, artist_config["sonic_pi_IP"], int(artist_config["sonic_pi_port"]))
        return feedback_message



