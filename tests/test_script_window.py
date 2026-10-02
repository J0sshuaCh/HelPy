import sys
import unittest
from PyQt5.QtWidgets import QApplication
from app.ui.script_window import ScriptWindow

app = QApplication.instance() or QApplication(sys.argv)

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

    def test_search_bar_extra_selections(self):
        window = ScriptWindow()
        window.md_view.setHtml("<h1>Título</h1><p>Este es un texto de prueba para búsqueda.</p>")
        window.search_bar.show_bar()
        window.search_bar.search_input.setText("prueba")
        
        # Verify extra selections were applied
        selections = window.md_view.extraSelections()
        self.assertGreater(len(selections), 0)
        
        # Verify text format/content was not destroyed
        self.assertIn("prueba", window.md_view.toPlainText())
        self.assertIn("Título", window.md_view.toPlainText())
        
        # Verify clear
        window.search_bar.clear_highlights()
        self.assertEqual(len(window.md_view.extraSelections()), 0)

    def test_search_bar_accessibility(self):
        window = ScriptWindow()
        self.assertTrue(len(window.search_bar.search_input.accessibleName()) > 0)
        self.assertTrue(len(window.search_bar.prev_btn.accessibleName()) > 0)
        self.assertTrue(len(window.search_bar.next_btn.accessibleName()) > 0)
        self.assertTrue(len(window.search_bar.close_btn.accessibleName()) > 0)

    def test_close_stops_autoscroll(self):
        window = ScriptWindow()
        window.auto_scroll.start()
        self.assertTrue(window.auto_scroll.is_active)
        window.close()
        self.assertFalse(window.auto_scroll.is_active)

if __name__ == '__main__':
    unittest.main()
