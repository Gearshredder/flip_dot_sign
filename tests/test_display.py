# test_display.py

import unittest
import sys
import os

# Ensure the parent directory is in the system path for importing mock_machine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mock_machine import MockMachine

class TestMockMachine(unittest.TestCase):
    def setUp(self):
        # Replace the machine module with the mock
        global machine
        machine = MockMachine()

    def test_pin(self):
        pin = machine.Pin(1, machine.Pin.OUT)
        pin.value(1)
        self.assertEqual(pin.value(), 1)
        pin.value(0)
        self.assertEqual(pin.value(), 0)

    def test_adc(self):
        adc = machine.ADC(0)
        adc.set_value(512)
        self.assertEqual(adc.read(), 512)
        adc.set_value(1023)
        self.assertEqual(adc.read(), 1023)

    def test_pwm(self):
        pwm = machine.PWM(2, freq=1000, duty=256)
        self.assertEqual(pwm.freq(), 1000)
        self.assertEqual(pwm.duty(), 256)
        
        pwm.duty(512)
        self.assertEqual(pwm.duty(), 512)

        pwm.freq(2000)
        self.assertEqual(pwm.freq(), 2000)

    def test_i2c(self):
        i2c = machine.I2C(0, scl=5, sda=4)
        i2c.writeto(0x50, [10, 20, 30])
        data = i2c.readfrom(0x50, 3)
        self.assertEqual(data, [10, 20, 30])

        # Test reading from an address with no data
        empty_data = i2c.readfrom(0x51, 3)
        self.assertEqual(empty_data, [0, 0, 0])

if __name__ == '__main__':
    unittest.main()
