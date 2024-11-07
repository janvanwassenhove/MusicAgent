from pythonosc import udp_client, dispatcher, osc_server
import threading
import time

class SonicPi:
    def __init__(self, logger):
        self.feedback_received = False
        self.feedback_message = ""
        self.logger = logger
        self.server = None
        self.server_thread = None

    def handle_message(self, address, *args):
        """Handles incoming OSC messages."""
        self.feedback_message = f"Received message from {address}: {args}"
        self.feedback_received = True
        self.logger.info(f"Received message from {address}: {args}")

    def shutdown_server(self):
        """Shuts down the OSC server."""
        if self.server and self.server_thread:
            print("Shutting down the server...")
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            self.server = None
            self.server_thread = None
            print("Server shut down successfully.")

    def read_script_from_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except Exception as e:
            print(f"Failed to read script from file {file_path}: {str(e)}")
            return None

    def call_sonicpi(self, song, ip_address, port):
        # Path to the Sonic Pi script file
        script_file_path = f"{song.song_dir}\\{song.name}.rb"
        self.logger.info("Script in path " + script_file_path)

        # Read the Sonic Pi script from the file
        full_script = self.read_script_from_file(script_file_path)

        self.logger.info(f"Running code in Sonic PI on {ip_address}:{port}")

        # Set up the OSC client to communicate with Sonic Pi
        client = udp_client.SimpleUDPClient(ip_address, port)

        # Attempt to shutdown any previous server instance
        try:
            self.shutdown_server()
        except AttributeError:
            pass  # First run, no server to shutdown

        # Set up OSC dispatcher to handle incoming messages
        disp = dispatcher.Dispatcher()
        disp.map("/feedback", self.handle_message)

        # Try to start the server on the desired port
        for attempt in range(3):  # Try 3 times
            try:
                self.server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", 4559), disp)
                self.server_thread = threading.Thread(target=self.server.serve_forever)
                self.server_thread.start()
                print("Server started successfully.")
                break  # If successful, break out of the loop
            except OSError as e:
                print(f"Error starting OSC server: {e}")

                if attempt < 2:  # If not the last attempt, retry
                    print(f"Port in use, retrying in 2 seconds... (Attempt {attempt + 1}/3)")

                    # Shutdown server before retrying if on second attempt
                    if attempt == 1:
                        self.shutdown_server()

                    time.sleep(2)
                else:  # If it's the last attempt, raise an error
                    print("Failed to start the server after 3 attempts.")
                    return

        self.logger.info("Script before sending: \n" + full_script)
        print(f"Sending \n" + full_script)
        client.send_message('/run-code', full_script)

        # Schedule the shutdown_server to run after 2 minutes
        shutdown_timer = threading.Timer(120, self.shutdown_server)
        shutdown_timer.start()

        # Wait for feedback, print message every 5 seconds
        start_time = time.time()
        while not self.feedback_received:
            elapsed_time = time.time() - start_time
            if elapsed_time >= 10:
                print(f"Waiting for response from Sonic PI - If you're not hearing anything... you might still need to run the recording code (Sonicpi/Setup) in your Sonic Pi IDE.")
                start_time = time.time()  # Reset the timer after printing the message
            time.sleep(0.1)

        # Print feedback message
        print(self.feedback_message)

        # Cancel the shutdown timer if feedback is received before the 2-minute mark
        shutdown_timer.cancel()

        # Shutdown server after receiving feedback
        self.shutdown_server()
