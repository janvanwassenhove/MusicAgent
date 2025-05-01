'''
This file contains the GPTAgent class that interacts with the OpenAI or Anthropic API to generate song lyrics.
'''

from openai import OpenAI
from openai import AzureOpenAI
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from .audiorecorder import AudioRecorder
from .songCreationData import SongCreationData
from .sonicPi import SonicPi
from pythonosc import udp_client, dispatcher as osc_dispatcher, osc_server
import tiktoken
import json
import os
import requests
import imghdr
import re
import threading
import time
import asyncio
import datetime
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from App.config import Config

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
        self.conversation_history = []
        provider_config = Config.MODEL_CONFIG.get(api_provider, {})
        model_config = provider_config.get(selected_model, {})
        self.max_context_length = model_config.get("content_length", 4096000)

    def log_request_response(self, provider, request_data, response_data, cost, token_count, char_count):
        songs_dir = os.path.join(Config.PROJECT_ROOT, 'Songs')
        if not os.path.exists(songs_dir):
            os.makedirs(songs_dir)
        song_log_directory = os.path.join(songs_dir, self.song.name)
        if not os.path.exists(song_log_directory):
            os.makedirs(song_log_directory)

        log_file = os.path.join(song_log_directory, 'api_requests.log')

        with open(log_file, 'a') as f:
            f.write(f"Timestamp: {datetime.datetime.now()}\n")
            f.write(f"Provider: {provider}\n")
            f.write(f"Request Data: {json.dumps(request_data, indent=2)}\n")
            f.write(f"Response Data: {json.dumps(response_data, indent=2)}\n")
            f.write(f"Cost: {cost}\n")
            f.write(f"Token Count: {token_count}\n")
            f.write(f"Character Count: {char_count}\n")
            f.write("\n" + "-"*80 + "\n\n")

    def count_tokens(self, content, model):
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("o200k_base")
        tokens = encoding.encode(content)
        return len(tokens)

    def check_token_limit(self, system_content, phase_prompt, model):
        provider_config = Config.MODEL_CONFIG.get(self.api_provider, {})
        model_config = provider_config.get(model, {})

        if not model_config:
            print(f"Model {model} not recognized for provider {self.api_provider}")
            return False

        combined_content = system_content + phase_prompt
        max_content_length = model_config.get("content_length")
        if len(combined_content) > max_content_length:
            print(f"Combined content length exceeds the maximum allowed length of {max_content_length} characters.")
            return False

        token_count = self.count_tokens(combined_content, model)
        max_tokens = model_config.get("tokens")
        if token_count <= max_tokens:
            print(f"Combined content is within the token limit for {model}. Token count: {token_count}, max is {max_tokens}")
            return True
        else:
            print(f"Combined content exceeds the token limit for {model}. Token count: {token_count}, max is {max_tokens}")
            return False

    def get_user_input(self, prompt):
        if self.input_callback:
            return self.input_callback(prompt)
        print("Input callback not set for webapp. Unable to get user input via modal.")
        return input(prompt)

    def get_api_key(self):
        return Config.get_api_key(self.api_provider)

    # Function to get assistant content from ArtistConfig
    def get_assistant_content(self, role_name, artist_config):
        for assistant in artist_config["assistants"]:
            if assistant["name"] == role_name:
                system_instructions = "\n".join(assistant["system_instruction"])
                if "sample_content" in assistant:
                    self.logger.info(f"additional content")
                return system_instructions
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
        elif task_type == "local_chat":
            self.local_discussion(client, phase, song_creation_data, artist_config, phase_config)
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

    def handle_anthropic_request(self, client, system_content, phase_prompt):
        request_data = {
            "model": self.selected_model,
            "system": system_content,
            "messages": [{"role": "user", "content": phase_prompt}],
            "max_tokens": self.MAX_TOKENS[self.selected_model]["tokens"]
        }
        completion = client.messages.create(**request_data)
        response_text = completion.content[0].text

        token_count = self.count_tokens(system_content + phase_prompt, self.selected_model)
        char_count = len(system_content + phase_prompt)
        cost = self.calculate_cost(token_count)
        self.log_request_response('anthropic', request_data, completion.content[0].text, cost, token_count, char_count)

        return response_text

    def handle_openai_request(self, client, system_content, phase_prompt, openai_messages):
        completion = client.chat.completions.create(
            model=self.selected_model,
            messages=openai_messages
        )
        response_text = completion.choices[0].message.content

        token_count = self.count_tokens(system_content + phase_prompt, self.selected_model)
        char_count = len(system_content + phase_prompt)
        cost = self.calculate_cost(token_count)

        self.log_request_response('openai', openai_messages, completion.choices[0].message.content, cost, token_count, char_count)
        return response_text

    def handle_azure_openai_request(self, client, system_content, phase_prompt, openai_messages):
        completion = client.chat.completions.create(
            model=self.selected_model,
            messages=openai_messages
        )
        response_text = completion.choices[0].message.content

        token_count = self.count_tokens(system_content + phase_prompt, self.selected_model)
        char_count = len(system_content + phase_prompt)
        cost = self.calculate_cost(token_count)

        self.log_request_response('openai', openai_messages, completion.choices[0].message.content, cost, token_count, char_count)
        return response_text

    def local_discussion(self, client, phase, song_creation_data, artist_config, phase_config):
        if phase not in phase_config:
            self.logger.info(f"No configuration found for phase: {phase}")
            return

        assistant_role_name = phase_config[phase]["assistant_role_name"]
        user_role_name = phase_config[phase]["user_role_name"]
        phase_prompt = ''.join(phase_config[phase]["phase_prompt"])

        # Replace placeholders in the prompt with actual values
        for key, value in phase_config[phase]["input"].items():
            param_value = song_creation_data.get_parameter(value)
            if param_value is not None:
                self.logger.info(f"Parameter for discussion [{key.upper()}]:[{param_value}]")
                phase_prompt = phase_prompt.replace(f"{{{key}}}", str(param_value))

        self.logger.info(
            f"Assistant is {assistant_role_name}, questioned by {user_role_name}. \nPrompting:\n {phase_prompt}\n"
        )

        project_root = Config.PROJECT_ROOT
        # Correct the path to the FAISS index file
        faiss_index_path = os.path.join(project_root, 'Samples', 'sample_index.faiss')
        metadata_path = os.path.join(project_root, 'Samples', 'sample_metadata.json')

        # Load the FAISS index and metadata
        index = faiss.read_index(faiss_index_path)
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Initialize the model for generating embeddings
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Generate an embedding for the query
        query = f"We are creating a new song with the following details: - Theme: {song_creation_data.theme}. " \
                f"- Melody: {song_creation_data.melody}. " \
                f"- Rhythm: {song_creation_data.rhythm}. " \
                f"- Song Description: {song_creation_data.song_description}. " \
                "Please suggest suitable samples with tags matching the mood, progression, and instrumentation described above."
        query_embedding = model.encode(query)  # Generate embedding locally
        query_embedding = np.array([query_embedding]).astype("float32")

        # Search for the nearest neighbors
        k = artist_config.get("samples_max", 5)  # Number of results to retrieve (reduced because of token limit)
        self.logger.info(f"Number of samples that will be retrieved: {k}")
        distances, indices = index.search(query_embedding, k)

        results = []
        for i in range(k):
            results.append(metadata[indices[0][i]])

        song_creation_data.samples = json.dumps(results, separators=(',', ':'))

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

        system_content = ''
        response_text = ''

        for assistant in artist_config["assistants"]:
            if assistant["name"] == assistant_role_name:
                print(f"found assistant {assistant_role_name}")
                system_instructions = "\n".join(assistant["system_instruction"])
                system_content = system_instructions

        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:

                if self.api_provider == 'openai':
                    openai_messages = [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": phase_prompt}
                    ]
                    if self.check_token_limit(system_content, phase_prompt, self.selected_model):
                        response_text = self.handle_openai_request(client, system_content, phase_prompt, openai_messages)
                elif self.api_provider == 'azure': #Azure
                    if self.check_token_limit(system_content, phase_prompt, self.selected_model):
                        response_text = self.handle_azure_openai_request(client, system_content, phase_prompt, openai_messages)
                elif self.api_provider == 'anthropic':  # Anthropic
                    if self.check_token_limit(system_content, phase_prompt, self.selected_model):
                        response_text = self.handle_anthropic_request(client, system_content, phase_prompt)

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

                    if code_to_retrieve and isinstance(code_to_retrieve, str):
                        fixed_code = self.fix_sonic_pi_notes(code_to_retrieve)
                    else:
                        print(f"Warning: code_to_retrieve is not a valid string. Value: {code_to_retrieve}")
                        fixed_code = code_to_retrieve 

                    self.logger.info(f"Code successfully retrieved: {fixed_code}")
                    song_creation_data.set_parameter("sonicpi_code", fixed_code)
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

    def fix_sonic_pi_notes(self, code):
        if not isinstance(code, str):  # Extra safeguard
            return code
        return re.sub(r":([A-G])#(\d)", lambda m: f":{m.group(1).lower()}s{m.group(2)}", code)

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
        project_root = Config.PROJECT_ROOT

        with open(os.path.join(project_root, 'AgentConfig', self.agentType, 'MusicCreationPhaseConfig.json')) as file:
            phase_config = json.load(file)
        with open(os.path.join(project_root, 'AgentConfig', self.agentType, 'MusicCreationChainConfig.json')) as file:
            compose_chain_config = json.load(file)
        with open(os.path.join(project_root, 'AgentConfig', self.agentType, 'ArtistConfig.json')) as file:
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
            quality="standard", # hd
        )

        # Extract image URL from response
        image_url = response.data[0].url
        self.logger.info("image " + image_url)

        if songdir == "":
            songdir = os.path.join(Config.PROJECT_ROOT, 'Songs', filename)
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

    def calculate_cost(self, token_count):
        provider_config = Config.MODEL_CONFIG.get(self.api_provider, {})
        model_config = provider_config.get(self.selected_model, {})
        price = model_config.get("price", 0.0001)  # Default fallback price
        return token_count * price

    def get_image_type(self, image_content):
        try:
            with Image.open(image_content) as img:
                return img.format  # Returns the image format (e.g., 'JPEG', 'PNG')
        except Exception as e:
            print(f"Error: {e}")
            return None

    def run_sonic_pi_script(self, song, artist_config):
        sonic_pi = SonicPi(self.logger)
        feedback_message = sonic_pi.call_sonicpi(self.song, Config.SONIC_PI_HOST, Config.SONIC_PI_PORT)
        return feedback_message

    def fix_sample_paths(self, sonic_pi_code: str) -> str:
        # Pattern matches sample file paths starting with the absolute Windows path.
        pattern = r'sample\s+"(?:[^"]*Samples\\\\)([^"]+)"'

        def repl(match):
            # Convert the captured relative path to use forward slashes.
            sample_relative = match.group(1).replace("\\", "/")
            return f'sample "{sample_relative}"'

        return re.sub(pattern, repl, sonic_pi_code)

    def handle_chat_input(self, sonic_pi_code, user_comment):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
        song_log_directory = os.path.join(root_dir, 'songs', self.song.name)
        conversation_file = os.path.join(song_log_directory, 'conversation_history.json')

        # Load existing conversation history
        if os.path.exists(conversation_file):
            with open(conversation_file, 'r') as file:
                conversation_history = json.load(file)
        else:
            conversation_history = []

        conversation_history.append({
            "role": "user",
            "content": user_comment
        })

        # Save updated conversation history
        with open(conversation_file, 'w') as file:
            json.dump(conversation_history, file, indent=2)

        # Convert system_content from a tuple to a string
        system_content = (
            "You are a creative music composer using Sonic Pi syntax. You respond to user suggestions by writing or editing Ruby code blocks for Sonic Pi."
            "Provide a response in **JSON format** with a field for \"sonicpi_code\". This field must contain the **entire Sonic Pi code** (not just the revisions or parts, but the full code for the entire song written in Ruby)."
            "Add a second field \"comment\" to include your feedback and comments on the code. E.g. what changed and some proposals for improvement of the song."
            "The response should be formatted as a JSON-compatible string, ready to be parsed. Format it as follows: {\"sonicpi_code\": \"<complete code here>\", \"comment\": \"<complete comment & feedback here>\"}."
            "Do not include any additional text, explanations, or comments outside of the JSON format."
            "Ensure the JSON strictly includes only the \"sonicpi_code\" and \"comment\" field, properly formatted and containing the final, complete code."
            "**GIVEN THIS INFORMATION, CODE SONGS USING THE SONIC PI PROGRAMMING LANGUAGE.**"
            "\n**KEY REQUIREMENTS:**"
            "1. **PARALLEL INSTRUMENTATION**: During key segments (e.g., verses, choruses, solos), ensure multiple instruments (e.g., melody, bassline, chords, and drum patterns) are **PLAYED SIMULTANEOUSLY** to create a **FULLER, RICHER SOUND**."
            "2. **BACKGROUND CONTINUITY**: Ensure background elements like drum patterns, recurring beats, or basslines **RUN CONTINUOUSLY** during segments to support the main melody or chords."
            "3. **DYNAMIC LAYERING**: During segments such as the **CHORUS**, introduce additional layers (e.g., harmony, effects like reverb or distortion, or more complex rhythms) to enhance the sound. Try having multiple sound patterns play in parallel like e.g. background synths, pads, and drums."
            "4. **NO SILENT GAPS**: The song must have a **CONTINUOUS, FLUENT MELODY** with no silent gaps or separate blocks."
            "5. **AVOID LIVE LOOPS**: Do not use live loops. Instead, use techniques like `in_thread`, `sync`, `sleep`, and timed sequences to manage the flow."
            "6. **TRANSLATION OF ARRANGEMENTS**: Translate the arrangements within the limitations of Sonic Pi, balancing instruments and effects effectively for each segment."
            "7. **SONIC PI SYNTAX**: Use Sonic Pi syntax and functions to create the song, ensuring it runs without errors."
            "8. **IN_THREAD USAGE**: Use `in_thread` to manage multiple instruments, to structure the song or effects running simultaneously, ensuring they are properly synchronized."
            "9. **SONG STRUCTURE**: The song should have a clear structure, including sections like intro, verse, chorus, bridge, and outro. Each section should be clearly defined and labeled in the code. The structure is depending on the song style or genre given in the prompt instructions."
            "\nThe composition should feel complete and cohesive, with a consistent tempo and flow."
        )

        sonic_pi_code = self.fix_sample_paths(sonic_pi_code)
        user_message = {
            "role": "user",
            "content": f"We have following song in Sonic PI code: {sonic_pi_code}. Code was reviewed with following comments: {user_comment}."
        }

        # Add conversation history to the user message
        conversation_history.append(user_message)
        conversation_history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])

        if self.api_provider == 'openai':
            client = OpenAI(api_key=self.get_api_key())
            messages = [
                {"role": "system", "content": system_content + "\n\n" + conversation_history_str},
                user_message
            ]
            self.logger.info(f"Sending request to OpenAI: {messages}")
            completion = client.chat.completions.create(
                model=self.selected_model,
                messages=messages
            )
            response_text = completion.choices[0].message.content

        elif self.api_provider == 'azure':
            client = OpenAI(
                # api_key=self.get_api_key(),
                api_version="2024-12-01-preview",
                # credential=
                # azure_endpoint=
                #azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), #https://musicagent.openai.azure.com/
                azure_deployment=self.selected_model
            )
            messages = [
                {"role": "system", "content": system_content + "\n\n" + conversation_history_str},
                user_message
            ]
            self.logger.info(f"Sending request to Azure OpenAI: {messages}")
            completion = client.chat.completions.create(
                model=self.selected_model,
                messages=messages
            )
            response_text = completion.choices[0].message.content

        elif self.api_provider == 'anthropic':
            client = Anthropic(api_key=self.get_api_key())
            request_data = {
                "model": self.selected_model,
                "prompt": system_content + "\n\n" + conversation_history_str + "\n\n" + user_message["content"],
                "max_tokens": self.MAX_TOKENS[self.selected_model]["tokens"]
            }
            self.logger.info(f"Sending request to Anthropic: {request_data}")
            completion = client.messages.create(**request_data)
            response_text = completion.content[0].text
        else:
            raise ValueError(f"Unsupported provider: {self.api_provider}")
        self.logger.info(f"Original response: {response_text}")

        # Append the assistant's response to the conversation history
        conversation_history.append({
            "role": "assistant",
            "content": response_text
        })

        # Save the updated conversation history
        with open(conversation_file, 'w') as file:
            json.dump(conversation_history, file, indent=2)

        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if match:
                    response_data = json.loads(match.group(0))
                else:
                    response_data = json.loads(response_text)

                if 'sonicpi_code' in response_data:
                    if isinstance(response_data['sonicpi_code'], list):
                        code_to_retrieve = '\n'.join(response_data['sonicpi_code'])
                    elif isinstance(response_data['sonicpi_code'], str):
                        code_to_retrieve = response_data['sonicpi_code']

                    if code_to_retrieve and isinstance(code_to_retrieve, str):
                        fixed_code = self.fix_sonic_pi_notes(code_to_retrieve)
                    else:
                        print(f"Warning: code_to_retrieve is not a valid string. Value: {code_to_retrieve}")
                        fixed_code = code_to_retrieve

                    self.logger.info(f"Code successfully retrieved: {fixed_code}")
                    self.song_creation_data.set_parameter("sonicpi_code", fixed_code)
                    self.song.create_song_file(self.song_creation_data)
                else:
                    song_creation_data.update_parameters_from_response(response_data)
                return response_data.get('comment', '')
            except json.JSONDecodeError as e:
                self.logger.info(f"Failed to parse the response as JSON: {e}")
                if self.handle_json_decode_error(response_text, self.song_creation_data, '', ''):
                    return response_data.get('comment', '')
                retry_count += 1