import sounddevice as sd

# List all available devices
devices = sd.query_devices()
print(devices)
# Print formatted device list exactly as it appears when querying all devices
print("Available devices:\n")

# Loop through all available devices and print them with driver type
for i, device in enumerate(devices):
    # Match formatting as printed when printing all devices at once
    device_repr = f"{i} {device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out)"
    print(device_repr)
