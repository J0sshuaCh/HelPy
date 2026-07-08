from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtWidgets import QApplication
from app.ui.shared import get_icon
from datetime import datetime


class TextDisplayPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._user_scrolled_up = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        
        self.transcription_label = QLabel("Transcripcion", self)
        self.transcription_label.setObjectName("sectionLabel")
        self.transcription_text = QTextEdit(self)
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setObjectName("textArea")
        self.transcription_text.setMaximumHeight(85)  # Aprox 4 lineas
        
        llm_header_row = QHBoxLayout()
        llm_header_row.setContentsMargins(0, 0, 0, 0)
        llm_header_row.setSpacing(6)
        self.llm_label = QLabel("Respuesta LLM", self)
        self.llm_label.setObjectName("sectionLabel")
        llm_header_row.addWidget(self.llm_label)
        llm_header_row.addStretch(1)
        
        self.copy_llm_button = QPushButton("", self)
        self.copy_llm_button.setObjectName("edgeButton")
        self.copy_llm_button.setIcon(get_icon("copy"))
        self.copy_llm_button.setIconSize(QSize(14, 14))
        self.copy_llm_button.setToolTip("Copiar respuesta al portapapeles")
        self.copy_llm_button.clicked.connect(self._copy_llm_text)
        llm_header_row.addWidget(self.copy_llm_button)
        
        self.export_button = QPushButton("", self)
        self.export_button.setObjectName("edgeButton")
        self.export_button.setIcon(get_icon("download"))
        self.export_button.setIconSize(QSize(14, 14))
        self.export_button.setToolTip("Exportar conversación a archivo (.md/.txt)")
        self.export_button.clicked.connect(self._export_conversation)
        llm_header_row.addWidget(self.export_button)
        
        self.llm_text = QTextEdit(self)
        self.llm_text.setReadOnly(True)
        self.llm_text.setObjectName("textArea")
        self.llm_min_height = 60
        self.llm_max_height = 260
        self.llm_text.setMinimumHeight(self.llm_min_height)
        self.llm_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Auto-scroll inteligente: detectar cuando el usuario scrollea arriba
        self.llm_text.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        
        self.layout.addWidget(self.transcription_label)
        self.layout.addWidget(self.transcription_text)
        self.layout.addLayout(llm_header_row)
        self.layout.addWidget(self.llm_text)
    
    def _on_scroll_changed(self, value):
        scrollbar = self.llm_text.verticalScrollBar()
        # Si el usuario está cerca del final (margen de 5px), consideramos que está abajo
        self._user_scrolled_up = value < scrollbar.maximum() - 5
    
    def _smart_scroll_to_bottom(self):
        """Solo hace scroll si el usuario no ha scrolleado arriba manualmente."""
        if not self._user_scrolled_up:
            scrollbar = self.llm_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _copy_llm_text(self):
        text = self.llm_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.copy_llm_button.setToolTip("Copiado!")
            QTimer.singleShot(1500, lambda: self.copy_llm_button.setToolTip("Copiar respuesta al portapapeles"))
    
    def _export_conversation(self):
        transcription = self.transcription_text.toPlainText().strip()
        llm_response = self.llm_text.toPlainText().strip()
        
        if not transcription and not llm_response:
            return
        
        # Generar contenido
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"# Conversación HelPy - {timestamp}\n\n"
        
        if transcription:
            content += f"## Transcripción\n\n{transcription}\n\n"
        
        if llm_response:
            content += f"## Respuesta IA\n\n{llm_response}\n"
        
        # Guardar archivo
        default_name = f"ayudin_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar conversación",
            default_name,
            "Markdown (*.md);;Texto plano (*.txt)"
        )
        
        if path:
            # Agregar extensión si no tiene
            if selected_filter.startswith("Markdown") and not path.endswith(".md"):
                path += ".md"
            elif selected_filter.startswith("Texto") and not path.endswith(".txt"):
                path += ".txt"
            
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.export_button.setToolTip("Exportado!")
                QTimer.singleShot(1500, lambda: self.export_button.setToolTip("Exportar conversación a archivo (.md/.txt)"))
            except Exception as e:
                print(f"Error al exportar: {e}")
