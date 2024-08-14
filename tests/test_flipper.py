# test_flipper.py

import unittest
from unittest.mock import patch
import sys
import os

# Ensure the parent directory is in the system path for importing flipper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.flipper import Display
from mock_machine import MockMachine, sleep_ms

class TestFlipper(unittest.TestCase):
    def setUp(self):
        global machine
        machine = MockMachine()

        # Patch the Pin class in the correct module path
        with patch('lib.flipper.Pin', machine.Pin):
            self.display = Display(modules=1)

    def test_flip_off(self):
        self.display.flip_off()
        self.assertEqual(self.display.erase_pin._value, 0)

    def test_flip_on(self):
        self.display.flip_on()
        self.assertEqual(self.display.write_pin._value, 0)

    def test_draw_dot(self):
        with patch.object(self.display, 'flip_on') as mock_flip_on, patch.object(self.display, 'flip_off') as mock_flip_off:
            self.display.draw_dot(x=2, y=3, z=0, write=True)
            mock_flip_on.assert_called_once()
            mock_flip_off.assert_not_called()

            self.display.draw_dot(x=2, y=3, z=0, write=False)
            mock_flip_off.assert_called_once()

    def test_write_dot_to_buffer(self):
        self.display.write_dot_to_buffer(2, 3, True)
        self.assertTrue(self.display.display_buffer1[3] & (1 << 2))

        self.display.write_dot_to_buffer(2, 3, False)
        self.assertFalse(self.display.display_buffer1[3] & (1 << 2))

    def test_draw_row(self):
        with patch.object(self.display, 'draw_dot') as mock_draw_dot:
            self.display.draw_row(0b1010101010101010101010101, 3)
            self.assertEqual(mock_draw_dot.call_count, 25)

    def test_write_row_fast(self):
        self.display.display_buffer1[3] = 0b0101010101010101010101010
        self.display.write_row_fast(0b1010101010101010101010101, 3)
        self.assertEqual(self.display.display_buffer1[3], 0b1111111111111111111111111)

    def test_write_row_to_buffer(self):
        self.display.display_buffer1[3] = 0b0101010101010101010101010
        with patch.object(self.display, 'draw_dot') as mock_draw_dot:
            self.display.write_row_to_buffer(0b1010101010101010101010101, 3)
            self.assertEqual(mock_draw_dot.call_count, 25)

    def test_draw_character(self):
        with patch.object(self.display, 'draw_row') as mock_draw_row:
            self.display.draw_character(self.display.checker1_char, 1)
            self.assertEqual(mock_draw_row.call_count, 7)

    def test_draw_character_fast(self):
        with patch.object(self.display, 'write_row_fast') as mock_write_row_fast:
            self.display.draw_character_fast(self.display.checker1_char, 1)
            self.assertEqual(mock_write_row_fast.call_count, 7)

    def test_write_character_to_buffer(self):
        with patch.object(self.display, 'write_dot_to_buffer') as mock_write_dot_to_buffer:
            self.display.write_character_to_buffer(self.display.checker1_char, 1)
            self.assertEqual(mock_write_dot_to_buffer.call_count, 35)

    def test_show(self):
        self.display.display_buffer1 = [0b1010101010101010101010101] * 7
        self.display.display_buffer2 = [0] * 7
        with patch.object(self.display, 'draw_dot') as mock_draw_dot:
            self.display.show()
            self.assertEqual(mock_draw_dot.call_count, 175)

    def test_fill(self):
        self.display.fill(1)
        self.assertEqual(self.display.display_buffer1[0], 0b1111111111111111111111111)

        self.display.fill(0)
        self.assertEqual(self.display.display_buffer1[0], 0b0)

    def test_clear_display_force(self):
        with patch.object(self.display, 'draw_row') as mock_draw_row:
            self.display.clear_display_force()
            self.assertEqual(mock_draw_row.call_count, 7)

if __name__ == '__main__':
    unittest.main()
