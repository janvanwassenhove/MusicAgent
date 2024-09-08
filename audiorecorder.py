import os
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import time
import threading
from sonicPi import SonicPi

class AudioRecorder:
    def __init__(self, logger, song, artist_config, fs=44100):
        self.song = song
        self.fs = fs
        self.artist_config = artist_config
        self.logger = logger

    def record_audio(self, duration, device=None):
        try:
            print(f"Recording on device {device}...")
            audio_data = sd.rec(int(duration * self.fs), samplerate=self.fs, channels=2, dtype='int16', device=device)
            sd.wait()  # Wait until the recording is finished
            print(f"Recording finished on device {device}")
            return audio_data
        except Exception as e:
            print(f"Failed to record on device {device}: {str(e)}")
            return None

    def start_recording(self, duration, device):
        audio_data = self.record_audio(duration, device=device)
        return audio_data

    # Main function to handle the recording process
    def run(self, duration, specific_device_index=None):
        print(f"Recording for device index {specific_device_index}...")

        devices = sd.query_devices()
        selected_device_index = None

        known_working_devices = [43]  # Add any other indices that have been tested and confirmed

        for device_id in known_working_devices:
            if device_id < len(devices):
                selected_device_index = device_id

        if selected_device_index is None:
            print("No suitable recording device found.")
            self.logger.error("No suitable recording device found for capturing output sound.")
            return

        output_wav_file = os.path.join(self.song.song_dir, f"{self.song.name}.wav")
        print(f"Attempting to record using device {selected_device_index}: {devices[selected_device_index]['name']}")

        sonic_pi = SonicPi(self.logger)

        # Shared variable to hold the recording result
        recording_result = {'audio_data': None}

        # Function to start recording and store the result
        def record_and_store():
            recording_result['audio_data'] = self.start_recording(duration, selected_device_index)

        # Start the recording thread
        recording_thread = threading.Thread(target=record_and_store)
        recording_thread.start()

        # Delay slightly to ensure the recording starts before playing the Sonic Pi script
        time.sleep(0.5)
        feedback_message = sonic_pi.call_sonicpi(self.song, self.artist_config["sonic_pi_IP"], int(self.artist_config["sonic_pi_port"]))
        if feedback_message is not None and "error" in feedback_message.lower():
            self.logger.info(f"Error detected in Sonic Pi execution: {feedback_message}")

        # Wait for the recording to finish
        recording_thread.join()

        # Retrieve the recorded audio data
        audio_data = recording_result['audio_data']
        if audio_data is not None:
            try:
                # Save the recording to a file
                write(output_wav_file, self.fs, audio_data)
                print(f"Recording saved to {output_wav_file}")
            except Exception as e:
                print(f"Error saving recording to {output_wav_file}: {str(e)}")
                self.logger.error(f"Failed to save recording: {e}")
        else:
            print(f"Skipping saving due to recording failure.")
