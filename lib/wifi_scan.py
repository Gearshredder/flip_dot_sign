import network

def scan_wifi_networks():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)  # Activate the interface
    networks = wlan.scan()

    if not networks:
        print("No WiFi networks available.")
        return

    print("Available networks:")
    for net in networks:
        ssid = net[0].decode('utf-8')  # Network SSID
        bssid = net[1]  # BSSID
        channel = net[2]  # Channel number
        RSSI = net[3]  # Signal strength
        authmode = net[4]  # Authentication mode
        hidden = net[5]  # Hidden SSID

        print("SSID:", ssid, "BSSID:", bssid, "Channel:", channel, "RSSI:", RSSI, "Auth mode:", authmode, "Hidden:", hidden)

# Run the function to scan and list networks
scan_wifi_networks()
