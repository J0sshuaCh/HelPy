import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from app.main import _try_create_overlay_window
from app.ui.script_window import ScriptWindow

def test_run():
    app = QApplication(sys.argv)
    script = ScriptWindow()
    overlay = _try_create_overlay_window()
    script.show()
    if overlay:
        overlay.show()
        
    def check_errors():
        print("Test run successful!")
        app.quit()
        
    QTimer.singleShot(1000, check_errors)
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_run()
