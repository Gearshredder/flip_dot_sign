# mock_machine.py

class MockPin:
    IN = 0
    OUT = 1
    PULL_UP = 2
    PULL_DOWN = 3

    def __init__(self, pin_number, mode, pull=None):
        self.pin_number = pin_number
        self.mode = mode
        self.pull = pull
        self._value = 0

    def on(self):
        self._value = 1

    def off(self):
        self._value = 0

    def value(self, val=None):
        if val is None:
            return self._value
        else:
            self._value = val


class MockADC:
    def __init__(self, pin):
        self.pin = pin
        self._value = 0

    def read(self):
        return self._value

    def set_value(self, val):
        self._value = val


class MockPWM:
    def __init__(self, pin, freq=500, duty=512):
        self.pin = pin
        self._freq = freq
        self._duty = duty

    def freq(self, freq=None):
        if freq is None:
            return self._freq
        else:
            self._freq = freq

    def duty(self, duty=None):
        if duty is None:
            return self._duty
        else:
            self._duty = duty

class MockI2C:
    def __init__(self, id, scl, sda, freq=100000):
        self.id = id
        self.scl = scl
        self.sda = sda
        self.freq = freq
        self.memory = {}

    def readfrom(self, addr, nbytes):
        return self.memory.get(addr, [0]*nbytes)

    def writeto(self, addr, buf):
        self.memory[addr] = buf

def sleep_ms(ms):
    # No-op function to simulate time delay in tests
    pass


class MockMachine:
    Pin = MockPin
    ADC = MockADC
    PWM = MockPWM
    I2C = MockI2C
    sleep_ms = sleep_ms
