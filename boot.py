# boot.py -- run on boot-up
import time
import machine

# Simple delay
time.sleep(5)

# Conditional delay based on a button press
#button = machine.Pin(0, machine.Pin.IN)

# Wait for button to be pressed to continue
#while button.value() == 0:
#    time.sleep(0.1)
