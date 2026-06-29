"""
Diálogo de onboarding para el primer lanzamiento de AYUDIN.
Guía al usuario en la configuración inicial: API keys, micrófono, hotkeys.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from app.ui.shared import get_icon


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bienvenido a AYUDIN")
        self.setMinimumSize(480, 400)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._current_step = 0
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Título
        self.title_label = QLabel("Bienvenido a AYUDIN", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Indicador de pasos
        self.step_indicator = QLabel("Paso 1 de 3", self)
        self.step_indicator.setAlignment(Qt.AlignCenter)
        self.step_indicator.setObjectName("statusLabel")
        layout.addWidget(self.step_indicator)
        
        # Contenido de pasos (stacked widget)
        self.steps_stack = QStackedWidget(self)
        self.steps_stack.addWidget(self._create_step1())
        self.steps_stack.addWidget(self._create_step2())
        self.steps_stack.addWidget(self._create_step3())
        layout.addWidget(self.steps_stack, 1)
        
        # Botones de navegación
        nav_layout = QHBoxLayout()
        nav_layout.addStretch(1)
        
        self.prev_btn = QPushButton("Anterior", self)
        self.prev_btn.setToolTip("Volver al paso anterior")
        self.prev_btn.clicked.connect(self._prev_step)
        self.prev_btn.setVisible(False)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Siguiente", self)
        self.next_btn.setToolTip("Avanzar al siguiente paso")
        self.next_btn.clicked.connect(self._next_step)
        nav_layout.addWidget(self.next_btn)
        
        self.close_btn = QPushButton("Cerrar", self)
        self.close_btn.setToolTip("Cerrar guía de inicio")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setVisible(False)
        nav_layout.addWidget(self.close_btn)
        
        layout.addLayout(nav_layout)
        
        # Botón skip
        skip_layout = QHBoxLayout()
        skip_layout.addStretch(1)
        self.skip_btn = QPushButton("Saltar guía", self)
        self.skip_btn.setToolTip("Cerrar esta guía y empezar a usar AYUDIN")
        self.skip_btn.setObjectName("statusLabel")
        self.skip_btn.clicked.connect(self.accept)
        skip_layout.addWidget(self.skip_btn)
        layout.addLayout(skip_layout)
    
    def _create_step1(self):
        """Paso 1: Configurar API Key"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("moon").pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title = QLabel("1. Configurar Proveedor de IA", self)
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        desc = QLabel(
            "Para empezar, necesitas configurar un proveedor de inteligencia artificial.\n\n"
            "Opciones disponibles:\n"
            "  • Google Gemini (requiere API key gratuita)\n"
            "  • Groq (requiere API key gratuita)\n"
            "  • LM Studio (local, sin API key)\n"
            "  • Local con llama.cpp (GPU/CPU, sin API key)\n\n"
            "Haz clic en 'Configurar LLM' en la ventana principal para agregar tu API key.",
            self
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignLeft)
        layout.addWidget(desc)
        
        layout.addStretch()
        return widget
    
    def _create_step2(self):
        """Paso 2: Verificar Micrófono"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("mic").pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title = QLabel("2. Verificar Micrófono", self)
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        desc = QLabel(
            "AYUDIN captura audio desde tu micrófono y/o el sistema.\n\n"
            "Pasos:\n"
            "  1. Selecciona tu micrófono en el panel de dispositivos\n"
            "  2. Haz clic en 'Grabar' para probar\n"
            "  3. Verifica que el nivel de audio suba en la barra VU\n\n"
            "Si no aparece ningún micrófono, verifica que esté conectado\n"
            "y que los permisos de audio estén habilitados.",
            self
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignLeft)
        layout.addWidget(desc)
        
        layout.addStretch()
        return widget
    
    def _create_step3(self):
        """Paso 3: Atajos de Teclado"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("expand").pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title = QLabel("3. Atajos de Teclado", self)
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        desc = QLabel(
            "AYUDIN tiene atajos globales que funcionan desde cualquier aplicación:\n\n"
            "  AltGr + G  →  Iniciar/Detener grabación\n"
            "  AltGr + \\  →  Enviar transcripción a la IA\n"
            "  AltGr + H  →  Colapsar/Expandir ventana\n"
            "  Ctrl + Espacio  →  Toggle grabación (ventana activa)\n"
            "  Escape  →  Cerrar ventana\n\n"
            "Estos atajos están disponibles incluso cuando la ventana\n"
            "no está enfocada. ¡Úsalos para ser productivo!",
            self
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignLeft)
        layout.addWidget(desc)
        
        layout.addStretch()
        return widget
    
    def _next_step(self):
        if self._current_step < 2:
            self._current_step += 1
            self.steps_stack.setCurrentIndex(self._current_step)
            self._update_ui()
    
    def _prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self.steps_stack.setCurrentIndex(self._current_step)
            self._update_ui()
    
    def _update_ui(self):
        total = 3
        self.step_indicator.setText(f"Paso {self._current_step + 1} de {total}")
        self.prev_btn.setVisible(self._current_step > 0)
        self.next_btn.setVisible(self._current_step < total - 1)
        self.close_btn.setVisible(self._current_step == total - 1)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self._current_step < 2:
                self._next_step()
            else:
                self.accept()
        super().keyPressEvent(event)
