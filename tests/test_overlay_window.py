import sys
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from app.ui.overlay_window import OverlayWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestOverlayWindow(unittest.TestCase):
    def test_overlay_window_instantiation(self):
        window = OverlayWindow()
        self.assertIsNotNone(window)
        self.assertEqual(window.position_mode, window.position_mode)
        
    def test_window_positioning_modes(self):
        window = OverlayWindow()
        window.set_position_mode("left")
        self.assertEqual(window.position_mode, "left")
        
    def test_collapse_expand(self):
        window = OverlayWindow()
        initial = window.is_collapsed
        window.toggle_collapsed()
        self.assertNotEqual(initial, window.is_collapsed)

    def test_accessibility_names_set(self):
        window = OverlayWindow()
        self.assertTrue(len(window.header_area.compact_button.accessibleName()) > 0)
        self.assertTrue(len(window.header_area.settings_button.accessibleName()) > 0)
        self.assertTrue(len(window.header_area.edge_button.accessibleName()) > 0)
        self.assertTrue(len(window.recording_panel.record_button.accessibleName()) > 0)
        self.assertTrue(len(window.text_display.copy_transcription_button.accessibleName()) > 0)
        self.assertTrue(len(window.text_display.copy_llm_button.accessibleName()) > 0)

    def test_preferences_dialog_escape_closes(self):
        window = OverlayWindow()
        window.open_preferences()
        self.assertTrue(window.preferences_dialog.isVisible())
        # Simulate pressing Escape on the preferences dialog
        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        window.preferences_dialog.keyPressEvent(event)
        self.assertFalse(window.preferences_dialog.isVisible())

    def test_audio_level_safe_signal(self):
        window = OverlayWindow()
        # Verify signal connection updates VU meter on Qt main thread safely
        window.audio_level_received.emit(0.75)
        self.assertAlmostEqual(window.recording_panel.vu_meter._level, 0.75)

if __name__ == '__main__':
    unittest.main()
