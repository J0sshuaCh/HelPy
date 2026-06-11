from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class PdfViewer(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setObjectName("pdfScroll")
        self.setStyleSheet("background: transparent; border: none;")
        
        self.pdf_container = QWidget()
        self.pdf_container.setObjectName("pdfContainer")
        self.pdf_container.setStyleSheet("background: transparent;")
        
        self.pdf_layout = QVBoxLayout(self.pdf_container)
        self.pdf_layout.setContentsMargins(0, 0, 0, 0)
        self.pdf_layout.setSpacing(10)
        self.pdf_layout.setAlignment(Qt.AlignHCenter)
        
        self.setWidget(self.pdf_container)
