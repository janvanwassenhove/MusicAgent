import logging
from pythonosc import udp_client

# Basic configuration for logging
logging.basicConfig(level=logging.INFO)

# Set up the OSC client for Sonic Pi
ip = "192.168.0.206"
port = 4560
client = udp_client.SimpleUDPClient(ip, port)

# Function to send OSC message with logging
def send_osc_message(address, message):
    try:
        client.send_message(address, message)
        logging.info(f"Sent message to {address}: {message}")
    except Exception as e:
        logging.error(f"Error sending OSC message: {e}")

# Example of sending a message
send_osc_message("/run-code", "play :C5")
send_osc_message("/run-code","define :bass_drop do |start_note = 60, end_note = 30, rate = 0.01| \n  use_synth :growl \n  play start_note, release: 3, note_slide: 3, amp: 10 \n  control change: rate \n  sleep 1 \n  use_synth :bnoise \n  play start_note, release: 3, note_slide: 3, amp: 2 \n  control change: rate \n  sleep 3 \nend \n \nbass_drop \n \ndefine :bass_drop2 do |start_note = 60, end_note = 30, rate = 0.01| \n  use_synth :cnoise \n  play start_note, release: 3, note_slide: 3, amp: 2 \n  control change: rate \n  sleep 3 \nend \n \nbass_drop2")

# Start a recording
client.send_message("/start-recording", [])
# Stop a recording
client.send_message("/stop-recording", [])
# Save a recording
client.send_message("/save-recording", ["test.wav"])
