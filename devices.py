import sounddevice as sd

# List all available devices
devices = sd.query_devices()
print(devices)
