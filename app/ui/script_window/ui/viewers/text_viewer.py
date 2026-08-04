from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor

class TextViewer(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("textArea")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        font = QFont("Segoe UI", 14)
        font.setStyleHint(QFont.SansSerif)
        self.setFont(font)

    def setMarkdown(self, text: str):
        super().setMarkdown(text)
        self._apply_document_font()

    def setPlainText(self, text: str):
        super().setPlainText(text)
        self._apply_document_font()

    def _apply_document_font(self):
        doc = self.document()
        f = QFont("Segoe UI", 14)
        f.setStyleHint(QFont.SansSerif)
        doc.setDefaultFont(f)
        self.moveCursor(QTextCursor.Start)
