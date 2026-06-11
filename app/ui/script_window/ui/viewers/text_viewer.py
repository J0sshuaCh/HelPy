from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt

class TextViewer(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("textArea")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
