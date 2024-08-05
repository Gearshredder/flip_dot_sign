import json
import time
from lib.wifi_manager import WifiManager
from lib.flipper import Display

# Load WiFi configuration from config.json
try:
    with open('config/config.json', 'r') as config_file:
        config = json.load(config_file)
        ssid = config['ssid']
        password = config['password']
        connection_type = 'sta'  # Station mode to connect to existing network
except Exception as e:
    print(f"Error loading config file: {e}")
    ssid = ''
    password = ''
    connection_type = ''

# Setup for the flip dot display
sign = Display(3)

# Load font configuration from font1.json
try:
    print("Trying to load font...")
    with open('font1.json', 'r') as font_file:
        ascii_dict = json.load(font_file)
        font = [ascii_dict[char][1:8] for char in range(123)]
        print("Font loaded")
except Exception as e:
    print(f"File or I/O error: {e}")
    font = None  # Use a default font or handle the error as required

# Fill and clear the sign to indicate boot up
sign.fill(1)  # Fill the sign (usually turns all dots on)
sign.show()   # Update the display to show the changes
sign.fill(0)  # Clear the sign (usually turns all dots off)
sign.show()   # Update the display to show the changes

# Initialize WiFi
wifi_manager = WifiManager(font, sign, ssid, password, connection_type)

# Start the WiFi interface
wifi_manager.start()

time.sleep(2)
