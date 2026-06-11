import sys
import unittest
from PyQt5.QtWidgets import QApplication
from app.ui.script_window import ScriptWindow

app = QApplication(sys.argv)

class TestScriptWindow(unittest.TestCase):
    def test_script_window_instantiation(self):
        window = ScriptWindow()
        self.assertIsNotNone(window)
        self.assertIsNotNone(window.file_loader)
        self.assertIsNotNone(window.zoom_manager)
        
    def test_collapse_expand(self):
        window = ScriptWindow()
        initial = window.is_collapsed
        window.toggle_collapsed()
        self.assertNotEqual(initial, window.is_collapsed)

    def test_capture_visibility(self):
        window = ScriptWindow()
        initial = window.capture_visible
        window.toggle_capture_visibility()
        self.assertNotEqual(initial, window.capture_visible)

if __name__ == '__main__':
    unittest.main()
