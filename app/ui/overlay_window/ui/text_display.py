from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtCore import Qt

class TextDisplayPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        
        self.transcription_label = QLabel("Transcripcion", self)
        self.transcription_label.setObjectName("sectionLabel")
        self.transcription_text = QTextEdit(self)
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setObjectName("textArea")
        self.transcription_text.setMaximumHeight(85)  # Aprox 4 lineas
        
        self.llm_label = QLabel("Respuesta LLM", self)
        self.llm_label.setObjectName("sectionLabel")
        self.llm_text = QTextEdit(self)
        self.llm_text.setReadOnly(True)
        self.llm_text.setObjectName("textArea")
        self.llm_min_height = 60
        self.llm_max_height = 260
        self.llm_text.setMinimumHeight(self.llm_min_height)
        self.llm_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.layout.addWidget(self.transcription_label)
        self.layout.addWidget(self.transcription_text)
        self.layout.addWidget(self.llm_label)
        self.layout.addWidget(self.llm_text)
