import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from pythonosc import udp_client
import time

# Function to record audio
def record_audio(duration, fs=44100, device=None):
    try:
        print(f"Recording on device {device}...")
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='int16', device=device)
        sd.wait()  # Wait until the recording is finished
        print(f"Recording finished on device {device}")
        return audio_data
    except Exception as e:
        print(f"Failed to record on device {device}: {str(e)}")
        return None

# Function to read Sonic Pi script from a file
def read_script_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Failed to read script from file {file_path}: {str(e)}")
        return None

# Set up the OSC client to communicate with Sonic Pi
client = udp_client.SimpleUDPClient("127.0.0.1", 4560)

# Path to the Sonic Pi script file
script_file_path = r"C:\Development\Workspaces\SongAgent\Songs\musicaly\muiscaly.rb"

# Read the Sonic Pi script from the file
full_script = read_script_from_file(script_file_path)

if full_script is None:
    print("Exiting due to failure in reading the script.")
    exit(1)

# Define the duration of the recording (adjust according to the script duration)
duration = 10  # Duration in seconds
fs = 44100  # Sampling rate

# Iterate over available audio devices and attempt recording
devices = sd.query_devices()
for i, device in enumerate(devices):
    if "Stereo Mix" in device['name'] or "Output" or "output" or "What You Hear" in device['name'] or "Loopback" in device['name']:
        if i == 43:
            output_wav_file = f"output_recording_device_{i}.wav"
            print(f"Attempting to record using device {i}: {device['name']}")

           # Replay the Sonic Pi script before each recording trial
            print("Sending script to Sonic Pi...")
            client.send_message('/run-code', full_script)

            audio_data = record_audio(duration, fs, device=i)

            # Give some time for Sonic Pi to start playing
            # time.sleep(0.5)  # Adjust this delay if necessary based on your needs

            if audio_data is not None:
                # Save the recording to a file if successful
                write(output_wav_file, fs, audio_data)
                print(f"Recording saved to {output_wav_file}")
            else:
                print(f"Skipping saving for device {i} due to recording failure.")
    else:
        print(f"Skipping device {i}: {device['name']} (not an output device)")
