import unittest
from unittest.mock import MagicMock, patch
from App.sonicPi import SonicPi
from App.song import Song
import logging
import time

class TestSonicPiIntegration(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("SonicPiTest")
        self.logger.setLevel(logging.INFO)
        self.sonic_pi = SonicPi(self.logger)
        self.song = Song(name="TestSong", logger=self.logger)
        self.song.song_dir = "test_dir"
        self.ip_address = "192.168.0.206"  # Replace with your Sonic Pi IP address
        self.port = 4560  # Replace with your Sonic Pi port
        self.full_script = "play 60"

    def test_call_sonicpi_integration(self):
        self.sonic_pi.call_sonicpi(self.song, self.ip_address, self.port, self.full_script)
        time.sleep(5)  # Wait for the script to execute and feedback to be received
        self.assertTrue(self.sonic_pi.feedback_received)
        self.assertIn("Received message from", self.sonic_pi.feedback_message)

if __name__ == '__main__':
    unittest.main()