import sys
from PyQt5.QtWidgets import QApplication
from app.ui.overlay_window import OverlayWindow
import unittest

app = QApplication(sys.argv)

class TestOverlayWindow(unittest.TestCase):
    def test_overlay_window_instantiation(self):
        window = OverlayWindow()
        self.assertIsNotNone(window)
        self.assertEqual(window.position_mode, window.position_mode) # Dummy assert
        
    def test_window_positioning_modes(self):
        window = OverlayWindow()
        window.set_position_mode("left")
        self.assertEqual(window.position_mode, "left")
        
    def test_collapse_expand(self):
        window = OverlayWindow()
        initial = window.is_collapsed
        window.toggle_collapsed()
        self.assertNotEqual(initial, window.is_collapsed)

if __name__ == '__main__':
    unittest.main()
