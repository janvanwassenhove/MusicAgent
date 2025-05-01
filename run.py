'''
The main file that will be executed to run the GPT agent for songwriting.
'''
import os
import logging
import json
from App.services.agent import GPTAgent
from App.services.song import Song

def get_available_models():
    return {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4", "gpt-4-32k"],
        "anthropic": ["claude-3-5-sonnet-20240620", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "azure": ["gpt-4o-mini"],
    }

def get_user_input(prompt, options):
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(options):
                selected = options[choice - 1]
                print(f"You have selected: {selected}")
                return selected
            else:
                print(f"Invalid selection. Please choose a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    print("\nWelcome to mITy John's music agent, let's make you a song!")

    # Get user input for provider
    available_providers = ["openai", "anthropic", "azure"]
    provider = get_user_input("Choose API provider:", available_providers)

    # Get user input for model
    available_models = get_available_models()[provider]
    selected_model = get_user_input(f"Choose a model for {provider}:", available_models)

    # Path to the directory
    directory_path = 'AgentConfig'

    # Get the list of folders
    available_models = [folder for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]

    # Display the available models
    print("Available Music Agent Configurations:")
    for i, model in enumerate(available_models, 1):
        print(f"{i}. {model}")

    # Prompt user to pick a model
    try:
        choice = int(input("Pick the music Agent configuration you want to use: "))
        if 1 <= choice <= len(available_models):
            agenttype = available_models[choice - 1]
            print(f"You have selected: {agenttype}")
        else:
            print("Invalid selection. Please choose a number from the list.")
    except ValueError:
        print("Invalid input. By default, the first model will be selected.")
        agenttype = available_models[0]

    print(f"Selected model: {agenttype}")

    # Load JSON data from the file
    with open("AgentConfig/"+agenttype+"/ArtistConfig.json", "r") as file:
        artist_config = json.load(file)

    # Get input parameters from the user
    song_name = input("\nEnter the name of the song: ")
    duration = get_valid_duration()
    genre = get_valid_style()

    additional_information = input("\nPlease add a description of you song (think musical influence, certain feelings that come up, ...) :")

    setup_logger(song_name)
    logger = logging.getLogger()
    logger.info("Starting Song Generation")

    # Create a GPT agent
    agent = GPTAgent(selected_model, logger, Song(song_name, logger), agenttype, provider)

    # Start the music composition chain
    agent.execute_composition_chain(genre, duration, additional_information)

def setup_logger(song_name):
    # Create 'songs' directory if it doesn't exist
    if not os.path.exists('Songs'):
        os.makedirs('Songs')
    # Create the subdirectory for the song
    song_directory = os.path.join('Songs', song_name)
    if not os.path.exists(song_directory):
        os.makedirs(song_directory)

    # Setting up the logger
    log_file = os.path.join(song_directory, 'music_agent.log')
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(message)s')

def get_valid_duration():
    return 180
    # while True:
    #     input_value = input("Enter the approximate duration of the song in seconds (or leave empty if you feel confident): ")
    #
    #     if input_value == "":
    #         return 180
    #     try:
    #         duration = int(input_value)
    #         if duration > 0:
    #             return duration
    #         else:
    #             print("Duration must be a positive integer.")
    #     except ValueError:
    #         print("Invalid duration. Please enter a valid integer.")

def load_json_data(key):
    file_path = 'AgentConfig/mITyJohn/SongConfig.json'
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get(key, [])
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing the file: {e}")
        return []

def get_user_choice(items, display_key, prompt, error_message):
    while True:
        print(prompt)
        for item in items:
            print(f"{item['id']}. {item[display_key]}")

        try:
            item_id = int(input("Enter your choice: "))
            selected_item = next((item for item in items if item['id'] == item_id), None)

            if selected_item:
                return selected_item[display_key]
            else:
                print(error_message)
        except ValueError:
            print("Please enter a valid integer.")

def get_valid_structure():
    structures = load_json_data('structures')
    return get_user_choice(structures, 'name',"What kind of song structures did you have in mind? Pick a number ;-)",
                           "Invalid ID. Please enter a valid ID.")

def get_valid_style():
    genres = load_json_data('genres')
    return get_user_choice(genres, 'genre',"What kind of style do you prefer? Please choose a number ;-)",
                           "Invalid ID. Please enter a valid ID.")

if __name__ == "__main__":
    main()