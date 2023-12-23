'''
This file contains the GPTAgent class that interacts with the OpenAI API to generate song lyrics.
'''
import os
import requests
from openai import OpenAI
class GPTAgent:
    def __init__(self, api_key, selected_model):
        self.api_key = api_key
        self.selected_model = selected_model

    def validate_sonicpi(self, lyrics):
        client = OpenAI()
        client.api_key = self.api_key

        prompt = ("Validate the following sonic pi code and correct where needed "
                  "to make sure it compiles and can be ran in sonic pi IDE: \n" + lyrics + "\n"
                  "Make sure only simple loops and threads are used, if live_loop is used, you should replace it or use conditionals to manage timing. ")

        completion = client.chat.completions.create(
            model=self.selected_model,
            messages=[
                {"role": "system", "content": "You validate and test code written in sonic pi. You'll only verify and correct if needed an return only the code. "
                                              "If no corrections are needed, you'll return the original prompted script. Code explanation is added in comment."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract Sonic Pi script from the response
        response_text = completion.choices[0].message.content
        script_start = response_text.find('```ruby') + len('```ruby\n')
        script_end = response_text.find('```', script_start)
        if script_start != -1 and script_end != -1:
            print("Corrections were needed.")
            lyrics = response_text[script_start:script_end].strip()
        else:
            print("No corrections were needed.")
        return lyrics
    def generate_lyrics(self, song_name, duration, structure, style_description, additional_information):
        print("\n ----------------------------------------------------------------------------------\n")
        print(" Let's get started with your music agent *** mITy.John *** \n")
        print(" Song: '" + song_name +"'")
        print(" Structure: " + structure + "")
        print(" Genre: " + style_description + "")
        print(" Duration: " + str(duration) + " seconds")
        print(" Additional info: " + additional_information + "")
        print("\n ----------------------------------------------------------------------------------\n")

        # Generate the song lyrics using the OpenAI API
        lyrics = self.generate_music_code(structure, style_description, duration, additional_information)
        return lyrics
    def generate_music_code(self, song_structure, genre, duration, additional_information):

        client = OpenAI()
        client.api_key = self.api_key

        while True:
            base_prompt = (f"Create a Sonic Pi script that plays a song with the following structure: {song_structure}. "
                           "The script should use simple loops and threads, and should not use live_loop. Ensure the song has a clear start and end.")
            prompt_with_config = (base_prompt + " As a genre for the song, please use "
                                  + genre + ". Incorporate multiple sounds in parallel, but make sure the entire composition takes "
                                  + str(duration) + " seconds (use sleep, ADSR, in_thread or Live Loops with Conditionals to manage timing, and provide specific durations for each section of the song)."
                                                    " Break down your song structure  into time segments that add up to  " + str(duration) + " seconds."
                                                    " Within each section, ensure that the sum of all sleep durations equals the allocated time for that section. "
                                                    " Use in_thread to create concurrent threads. Each thread can have its own timing, but make sure the total duration of each thread is synchronized with the overall song duration."                                                                                                                                         
                                                    " The script should have a clear start and end, emphasizing a harmonious blend of sounds characteristic of " + genre + ".")

            if additional_information:
                prompt = prompt_with_config + " Finally, consider the following: " + additional_information
            else:
                prompt = prompt_with_config

            print("\nPrompting OpenAI: ")
            print(prompt)
            completion = client.chat.completions.create(
                model=self.selected_model,
                messages=[
                    {"role": "system", "content": "You are a songwriter, skilled in creating song programmed in sonic pi. "
                                                  "You create and program songs using Sonic PI. You know the song basic structure: intro, verse — chorus — verse — chorus — bridge — chorus — outro. "
                                                  "Your songs duration varies between 2 & 4 minutes. You like to use multiple sounds in parallel."
                                                  "Don't use live_loop in Sonic PI script, use simple loops and threads instead. The song clearly ends & starts."},
                    {"role": "user", "content": prompt}
                ]
            )
            # Extract Sonic Pi script from the response
            response_text = completion.choices[0].message.content
            script_start = response_text.find('```ruby') + len('```ruby\n')
            script_end = response_text.find('```', script_start)
            sonic_pi_script = response_text[script_start:script_end].strip()

            # Check if the script contains valid Sonic Pi code
            if 'play' in sonic_pi_script or 'sleep' in sonic_pi_script:  # Add more checks as needed
                break

        return sonic_pi_script