import time
import network
import ntptime
import socket
from machine import RTC, Timer

class WifiManager:
    def __init__(self, font, sign, ssid, password, connection_type):
        self.sign = sign
        self.ssid = ssid
        self.password = password
        self.font = font
        self.connection_type = connection_type
        self.time_mode_active = False
        self.timer = None
        self.station = None
        self.s = None

    def start(self):
        # Initialize the WLAN interface based on the connection type
        if self.connection_type == "ap":
            self.station = network.WLAN(network.AP_IF)
        elif self.connection_type == "sta":
            self.station = network.WLAN(network.STA_IF)
        else:
            print("Invalid connection type specified.")
            return

        print("Starting WiFi...")

        # Reset the WLAN interface
        self.station.active(False)
        time.sleep(1)  # Short delay for proper reset
        self.station.active(True)

        # Configure for Access Point (AP) mode
        if self.connection_type == "ap":
            self.station.config(essid=self.ssid, password=self.password, authmode=4)  # Set AP config
            self.station.active(True)  # Then activate the AP
            while not self.station.active():
                pass
            print('AP Mode Connection successful')
            print(self.station.ifconfig())

        # Configure for Station (STA) mode
        elif self.connection_type == "sta":
            print("Connecting to SSID:", self.ssid)
            self.station.connect(self.ssid, self.password)

            timeout = 20  # Timeout in seconds
            start_time = time.time()

            while not self.station.isconnected():
                if time.time() - start_time > timeout:
                    print("STA Mode Connection failed: Timeout after", timeout, "seconds.")
                    break
                print("Attempting to connect (Elapsed time:", round(time.time() - start_time, 2), "seconds)")
                time.sleep(1)

            if self.station.isconnected():
                print('STA Mode Connection successful')
                print(self.station.ifconfig())
            else:
                print("Failed to connect to SSID:", self.ssid)
                
        # Close existing socket if it's open
        if self.s is not None:
            try:
                self.s.close()
            except Exception as e:
                print("Error closing socket:", e)
            self.s = None

        # Socket setup for both AP and STA mode
        try:
            print('Setting up socket...')
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind(('', 80))
            self.s.listen(5)
            print('Socket listening on port 80')
            self.run_server()
        except Exception as e:
            print("Failed to create socket:", e)
            self.s = None

    def run_server(self):
        while True:
            conn, addr = self.s.accept()
            conn.settimeout(5)
            print('Client connected from', addr)
            try:
                request = conn.recv(1024)
                if not request:
                    print("No data received. Closing connection.")
                    conn.close()
                    continue

                request = request.decode('utf-8')
                print('Received request:', request)
                response = self.web_page()
                conn.sendall(b'HTTP/1.1 200 OK\n')
                conn.sendall(b'Content-Type: text/html\n')
                conn.sendall(b'Connection: close\n\n')
                conn.sendall(response.encode())
            except Exception as e:
                print("Error handling socket connection:", e)
            finally:
                conn.close()
                print("Connection with client closed.")

    def web_page(self):
        html = """
        <html>
            <head>
                <title>FLIP DOT SIGN</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link rel="icon" href="data:,">
                <style>
                    html {
                        font-family: Helvetica; 
                        display: inline-block; 
                        margin: 0px auto; 
                        text-align: center;
                    }
                    h1 {
                        color: #0F3376; 
                        padding: 2vh;
                    }
                    p {
                        font-size: 1.5rem;
                    }
                    .button {
                        display: inline-block; 
                        background-color: #e7bd3b; 
                        border: none; 
                        border-radius: 4px; 
                        color: white; 
                        padding: 16px 40px; 
                        text-decoration: none; 
                        font-size: 30px; 
                        margin: 2px; 
                        cursor: pointer;
                    }
                    .button2 {
                        background-color: #4286f4;
                    }
                </style>
            </head>
            <body>
                <h1>Flip Dot Sign</h1>
                <form action="/" method="GET">
                    <div>
                        <input type="radio" id="text_mode" name="mode" value="text">
                        <label for="text_mode">Text Mode</label>
                    </div>
                    <div>
                        <input type="radio" id="time_mode" name="mode" value="time">
                        <label for="time_mode">Time Mode</label>
                    </div>
                    <div>
                        <input type="radio" id="scroll_mode" name="mode" value="scroll">
                        <label for="scroll_mode">Scrolling Text Mode</label>
                    </div>
                    <div>
                        <label for="scroll_text">Scrolling Text (separate lines with a newline):</label>
                        <textarea id="scroll_text" name="scroll_text"></textarea>
                    </div>
                    <div>
                        <label for="entry">Type some text:</label>
                        <input type="text" id="entry" name="entry" minlength="1" maxlength="15">
                    </div>
                    <button type="submit">Submit</button>
                </form>
            </body>
        </html>"""
        return html

    def set_time_from_ntp(self, max_attempts=3, timeout=5):
        attempt = 0
        while attempt < max_attempts:
            try:
                ntptime.host = 'pool.ntp.org'  # You can try different NTP servers
                ntptime.settime()  # Attempt to set the system time to NTP time
                rtc = RTC()
                print("Time successfully synchronized with NTP server.")
                return rtc.datetime()  # Return the current time
            except Exception as e:
                print(f"Attempt {attempt + 1} failed to get time from NTP. Error: {str(e)}")
                attempt += 1
                time.sleep(timeout)  # Wait before retrying

        print("Failed to synchronize time after several attempts.")
        return None
