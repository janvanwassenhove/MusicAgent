'''
The main file that will be executed to run the GPT agent for songwriting.
'''
import os
import openai
import json
from agent import GPTAgent
from song import Song

def main():

    print("\nWelcome to mITy John's music agent, let's make you a song!")
    print("First let get you started, providing me some options to consider.")

    # List of available OpenAI models
    available_models = ["gpt-3.5-turbo", "gpt-4", "curie", "babbage", "ada"]

    # Display the available models
    print("\nAvailable OpenAI models:")
    for index, model in enumerate(available_models, start=1):
        print(f"{index}. {model}")

    # Initialize the default model
    selected_model = "davinci"

    # Prompt the user to pick a model
    try:
        choice = int(input("Pick a number of the model to use: "))
        if 1 <= choice <= len(available_models):
            selected_model = available_models[choice - 1]
            print(f"You have selected: {selected_model}")
        else:
            print("Invalid selection. Please choose a number from the list.")
    except ValueError:
        print("Invalid input. By default davinci will be chosen.")
        pass

    # Get input parameters from the user
    song_name = input("\nEnter the name of the song: ")
    structure = get_valid_structure()
    duration = get_valid_duration(structure)
    genre = get_valid_style()

    additional_information = input("\nPlease add some additional information (if you wanna go wild, leave blank :-) ):")

    # Create a GPT agent
    agent = GPTAgent(get_api_key(), selected_model)

    # Generate song lyrics using the GPT agent
    lyrics = agent.generate_lyrics(song_name, duration, structure, genre, additional_information)

    #double check if correctly written
    validatedLyrics = agent.validate_sonicpi(lyrics)

    # Create a Song object
    song = Song(song_name, duration, structure, genre, validatedLyrics)
    # Create the song file in the songs directory
    song.create_song_file()

def get_valid_duration(structurename):
    structures = load_json_data('structures')

    while True:
        input_value = input("Enter the approximate duration of the song in seconds (or leave empty if you feel confident): ")

        if input_value == "":
            for structure in structures:
                if structure["name"] == structurename:
                    print("Structure " + structurename)
                    return structure["duration"]
                else:
                    return 180
        try:
            duration = int(input_value)
            if duration > 0:
                return duration
            else:
                print("Duration must be a positive integer.")
        except ValueError:
            print("Invalid duration. Please enter a valid integer.")

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