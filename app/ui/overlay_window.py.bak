import sys
import ctypes
import time
import json
import os
from pathlib import Path

import sounddevice as sd
import soundcard as sc
from pynput import keyboard
from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QActionGroup,
    QPushButton,
    QComboBox,
    QTextEdit,
    QFrame,
    QButtonGroup,
    QLineEdit,
    QFormLayout,
    QFileDialog,
    QSlider,
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QScreen, QIcon, QPixmap, QColor, QPainter, QFont

from app.core.assistant_controller import AssistantController
from app.core.llm_client import get_llm_client
from app.ui.themes import PALETAS, obtener_qss
from app.utils.path_utils import asset_path, writable_config_path


class OverlayWindow(QWidget):
    text_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    llm_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.tray_icon = None
        self.recording = False
        self.is_collapsed = False
        self.position_mode = "right"  # "left", "center", "right"
        self.capture_visible = False
        # Drag handle logic: move entire window if clicking the header area
        self._drag_pos = QPoint()
        self.settings = self._load_settings()
        self.opacity = self.settings.get("overlay_opacity", 100)
        self.llm_config_collapsed = bool(self.settings.get("llm_config_collapsed", True))

        self.mic_devices = []
        self.sys_devices = []
        self.mic_menu = QMenu("Microfono")
        self.sys_menu = QMenu("Sistema")
        self.capture_mode = self.settings.get("capture_mode", "both")
        self.assistant = AssistantController(
            mic_device_index=None,
            system_device_index=None,
            capture_mode=self.capture_mode,
        )
        self.assistant.on_result(self._on_transcription_result)
        self.assistant.on_status(self._on_status_change)
        self.assistant.on_llm_result(self._on_llm_result)

        self.text_received.connect(self._set_transcription_safe)
        self.status_changed.connect(self._set_status_safe)
        self.llm_received.connect(self._set_llm_safe)

        # Create UI
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Header Area (New Title + Opacity + Buttons + Drag) - OUTSIDE container
        self.header_area = QFrame(self)
        self.header_area.setObjectName("headerArea")
        header_layout = QHBoxLayout(self.header_area)
        header_layout.setContentsMargins(10, 10, 10, 2)
        header_layout.setSpacing(5)
        
        title_label = QLabel("HelPy")
        title_label.setObjectName("appTitle")
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(self.opacity)
        self.opacity_slider.setFixedWidth(100)
        self.opacity_slider.valueChanged.connect(self._apply_global_opacity)
        self.opacity_slider.setObjectName("opacitySlider")
        
        self.capture_button = QPushButton("", self)
        self.capture_button.setObjectName("edgeButton")
        self.capture_button.setIcon(self._icon("eye_off"))
        self.capture_button.setIconSize(QSize(14, 14))
        self.capture_button.clicked.connect(self.toggle_capture_visibility)

        self.edge_button = QPushButton("", self)
        self.edge_button.setObjectName("edgeButton")
        self.edge_button.setIcon(self._icon("collapse"))
        self.edge_button.setIconSize(QSize(14, 14))
        self.edge_button.clicked.connect(self.toggle_collapsed)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.capture_button)
        header_layout.addWidget(self.edge_button)
        
        self.main_layout.addWidget(self.header_area)

        # Container for the rest of UI
        self.container = QFrame(self)
        self.container.setObjectName("overlayContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 5, 16, 16)
        container_layout.setSpacing(10)
        
        # 2. Position Buttons Row (Inside container to be collapsed)
        pos_row = QHBoxLayout()
        pos_row.setContentsMargins(0, 0, 0, 0)
        
        self.pos_left_btn = QPushButton("", self)
        self.pos_left_btn.setObjectName("edgeButton")
        self.pos_left_btn.setIcon(self._icon("arrow_left"))
        self.pos_left_btn.setIconSize(QSize(14, 14))
        self.pos_left_btn.clicked.connect(lambda: self.set_position_mode("left"))
        
        self.pos_center_btn = QPushButton("", self)
        self.pos_center_btn.setObjectName("edgeButton")
        self.pos_center_btn.setIcon(self._icon("arrow_up"))
        self.pos_center_btn.setIconSize(QSize(14, 14))
        self.pos_center_btn.clicked.connect(lambda: self.set_position_mode("center"))
        
        self.pos_right_btn = QPushButton("", self)
        self.pos_right_btn.setObjectName("edgeButton")
        self.pos_right_btn.setIcon(self._icon("arrow_right"))
        self.pos_right_btn.setIconSize(QSize(14, 14))
        self.pos_right_btn.clicked.connect(lambda: self.set_position_mode("right"))

        pos_row.addWidget(self.pos_left_btn)
        pos_row.addWidget(self.pos_center_btn)
        pos_row.addWidget(self.pos_right_btn)
        pos_row.addStretch(1)
        pos_row.addWidget(QLabel("Opacidad:"))
        pos_row.addWidget(self.opacity_slider)
        container_layout.addLayout(pos_row)

        # 3. Rest of the UI
        device_row = QHBoxLayout()
        device_row.setSpacing(10)
        self.mic_combo = QComboBox(self)
        self.mic_combo.setObjectName("deviceCombo")
        self.sys_combo = QComboBox(self)
        self.sys_combo.setObjectName("deviceCombo")
        device_row.addWidget(self.mic_combo, 1)
        device_row.addWidget(self.sys_combo, 1)
        container_layout.addLayout(device_row)

        capture_row = QHBoxLayout()
        capture_row.setSpacing(10)

        self.capture_mode_group = QButtonGroup(self)
        self.capture_mode_group.setExclusive(True)

        self.capture_mic_btn = QPushButton("Mic", self)
        self.capture_mic_btn.setObjectName("modeButton")
        self.capture_mic_btn.setCheckable(True)
        self.capture_mic_btn.setIcon(self._icon("mic"))
        self.capture_mic_btn.setIconSize(QSize(16, 16))
        self.capture_mic_btn.setToolTip("Solo microfono")
        self.capture_mic_btn.clicked.connect(lambda: self.set_capture_mode("mic"))

        self.capture_sys_btn = QPushButton("Equipo", self)
        self.capture_sys_btn.setObjectName("modeButton")
        self.capture_sys_btn.setCheckable(True)
        self.capture_sys_btn.setIcon(self._icon("monitor"))
        self.capture_sys_btn.setIconSize(QSize(16, 16))
        self.capture_sys_btn.setToolTip("Solo audio del equipo")
        self.capture_sys_btn.clicked.connect(lambda: self.set_capture_mode("system"))

        self.capture_both_btn = QPushButton("Ambos", self)
        self.capture_both_btn.setObjectName("modeButton")
        self.capture_both_btn.setCheckable(True)
        self.capture_both_btn.setIcon(self._icon("mic_monitor"))
        self.capture_both_btn.setIconSize(QSize(16, 16))
        self.capture_both_btn.setToolTip("Microfono y sistema")
        self.capture_both_btn.clicked.connect(lambda: self.set_capture_mode("both"))

        self.capture_mode_group.addButton(self.capture_mic_btn)
        self.capture_mode_group.addButton(self.capture_sys_btn)
        self.capture_mode_group.addButton(self.capture_both_btn)

        capture_row.addWidget(self.capture_mic_btn, 1)
        capture_row.addWidget(self.capture_sys_btn, 1)
        capture_row.addWidget(self.capture_both_btn, 1)
        container_layout.addLayout(capture_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.record_button = QPushButton("Grabar", self)
        self.record_button.clicked.connect(self.toggle_recording)
        self.send_button = QPushButton("Enviar a LLM", self)
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.assistant.send_buffer_to_llm)
        self.refresh_button = QPushButton("Actualizar dispositivos", self)
        self.refresh_button.clicked.connect(self._build_device_menus)
        button_row.addWidget(self.record_button)
        button_row.addWidget(self.send_button)
        button_row.addWidget(self.refresh_button)
        container_layout.addLayout(button_row)

        self.status_label = QLabel("Estado: listo", self)
        self.status_label.setObjectName("statusLabel")
        container_layout.addWidget(self.status_label)

        self.warning_label = QLabel("", self)
        self.warning_label.setObjectName("warningLabel")
        self.warning_label.setVisible(False)
        container_layout.addWidget(self.warning_label)

        # AI Configuration Section
        ai_config_group = QFrame(self)
        ai_config_group.setObjectName("aiConfigGroup")
        ai_config_layout = QVBoxLayout()
        ai_config_layout.setContentsMargins(0, 0, 0, 0)
        ai_config_group.setLayout(ai_config_layout)

        ai_header_row = QHBoxLayout()
        ai_header_row.setContentsMargins(0, 0, 0, 0)
        self.llm_toggle_button = QPushButton("Configurar LLM:", self)
        self.llm_toggle_button.setObjectName("sectionToggle")
        self.llm_toggle_button.clicked.connect(self.toggle_llm_config)
        
        self.selector_temas = QComboBox(self)
        self.selector_temas.setObjectName("deviceCombo")
        self.selector_temas.addItems(list(PALETAS.keys()))
        self.selector_temas.currentTextChanged.connect(self.cambiar_tema_interfaz)
        
        ai_header_row.addWidget(self.llm_toggle_button, 0)
        ai_header_row.addWidget(self.selector_temas, 0)
        ai_header_row.addStretch(1)
        ai_config_layout.addLayout(ai_header_row)

        self.ai_config_body = QFrame(self)
        self.ai_config_body.setObjectName("aiConfigBody")
        ai_form_layout = QFormLayout()
        ai_form_layout.setSpacing(10)
        ai_form_layout.setContentsMargins(12, 8, 12, 12)

        self.ai_provider_combo = QComboBox(self)
        self.ai_provider_combo.setObjectName("deviceCombo")
        self.ai_provider_combo.addItems(["LM Studio", "Google", "Groq", "Local (llama.cpp)"])
        ai_form_layout.addRow("Proveedor:", self.ai_provider_combo)

        self.api_key_input = QLineEdit(self)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        ai_form_layout.addRow("API Key:", self.api_key_input)

        self.model_id_input = QLineEdit(self)
        self.model_id_input.setPlaceholderText("Opcional: openai/gpt-oss-120b")
        model_container = QWidget(self)
        model_row = QHBoxLayout(model_container)
        model_row.setContentsMargins(0, 0, 0, 0)
        model_row.addWidget(self.model_id_input, 1)
        self.browse_model_btn = QPushButton("Examinar...", self)
        self.browse_model_btn.clicked.connect(self._browse_model)
        self.download_model_btn = QPushButton("Descargar modelo", self)
        self.download_model_btn.setObjectName("downloadModelBtn")
        self.download_model_btn.clicked.connect(self._download_model)
        self.download_model_btn.setVisible(False)
        model_row.addWidget(self.browse_model_btn, 0)
        model_row.addWidget(self.download_model_btn, 0)
        ai_form_layout.addRow("Model ID:", model_container)

        ai_button_row = QHBoxLayout()
        self.save_ai_button = QPushButton("Guardar", self)
        self.save_ai_button.setObjectName("saveAIButton")
        self.save_ai_button.clicked.connect(self._save_ai_settings)
        self.ai_status_label = QLabel("", self)
        self.ai_status_label.setObjectName("statusLabel")
        ai_button_row.addWidget(self.ai_status_label)
        ai_button_row.addStretch(1)
        ai_button_row.addWidget(self.save_ai_button)

        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addLayout(ai_form_layout)
        body_layout.addLayout(ai_button_row)
        self.ai_config_body.setLayout(body_layout)
        ai_config_layout.addWidget(self.ai_config_body)

        container_layout.addWidget(ai_config_group)

        self.text_container = QFrame(self)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)
        self.text_container.setLayout(text_layout)

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
        self._llm_min_height = 60
        self._llm_max_height = 260
        self.llm_text.setMinimumHeight(self._llm_min_height)
        self.llm_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.llm_text.document().contentsChanged.connect(self._update_llm_height)
        self._update_llm_height()

        text_layout.addWidget(self.transcription_label)
        text_layout.addWidget(self.transcription_text)
        text_layout.addWidget(self.llm_label)
        text_layout.addWidget(self.llm_text)
        container_layout.addWidget(self.text_container)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.container)

        self._load_ai_settings()
        self.ai_provider_combo.currentIndexChanged.connect(self._on_ai_provider_changed)
        self._apply_llm_config_visibility()
        
        # Tema inicial
        tema_guardado = self.settings.get("tema", "Slate Minimalist")
        self.selector_temas.setCurrentText(tema_guardado)
        self.cambiar_tema_interfaz(tema_guardado)
        
        self._build_device_menus()
        self._apply_window_size()
        
        self.show()
        self.adjustSize()
        self.update_position()

        self._apply_capture_affinity()

    def init_tray_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 120, 215))
        icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(icon, self)

        menu = QMenu()
        self.record_action = menu.addAction("Iniciar grabacion")
        self.record_action.triggered.connect(self.toggle_recording)
        menu.addSeparator()

        devices_action = menu.addAction("Dispositivos")
        devices_menu = QMenu()
        devices_action.setMenu(devices_menu)
        self.mic_menu = QMenu("Microfono")
        self.sys_menu = QMenu("Sistema")
        devices_menu.addMenu(self.mic_menu)
        devices_menu.addMenu(self.sys_menu)
        self._build_device_menus()

        self.loopback_action = menu.addAction("Loopback soportado: ?")
        self.loopback_action.setEnabled(False)

        capture_mode_action = menu.addAction("Modo captura")
        capture_mode_menu = QMenu()
        capture_mode_action.setMenu(capture_mode_menu)

        self.capture_mode_group_tray = QActionGroup(self)
        self.capture_mode_group_tray.setExclusive(True)

        self.capture_mode_mic_action = QAction("Microfono", self)
        self.capture_mode_mic_action.setCheckable(True)
        self.capture_mode_mic_action.setIcon(self._icon("mic"))
        self.capture_mode_mic_action.triggered.connect(lambda: self.set_capture_mode("mic"))

        self.capture_mode_sys_action = QAction("Equipo", self)
        self.capture_mode_sys_action.setCheckable(True)
        self.capture_mode_sys_action.setIcon(self._icon("monitor"))
        self.capture_mode_sys_action.triggered.connect(lambda: self.set_capture_mode("system"))

        self.capture_mode_both_action = QAction("Ambos", self)
        self.capture_mode_both_action.setCheckable(True)
        self.capture_mode_both_action.setIcon(self._icon("mic_monitor"))
        self.capture_mode_both_action.triggered.connect(lambda: self.set_capture_mode("both"))

        self.capture_mode_group_tray.addAction(self.capture_mode_mic_action)
        self.capture_mode_group_tray.addAction(self.capture_mode_sys_action)
        self.capture_mode_group_tray.addAction(self.capture_mode_both_action)

        capture_mode_menu.addAction(self.capture_mode_mic_action)
        capture_mode_menu.addAction(self.capture_mode_sys_action)
        capture_mode_menu.addAction(self.capture_mode_both_action)

        mic_mode_action = menu.addAction("Modo microfono: Auto")
        mic_mode_action.triggered.connect(self.toggle_mic_mode)
        self.mic_mode_action = mic_mode_action
        menu.addSeparator()
        quit_action = menu.addAction("Salir")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self._update_loopback_status()

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()


    def start_recording(self):
        self.recording = True
        if hasattr(self, "record_action"):
            self.record_action.setText("Detener grabacion")
            self.record_action.setIcon(QIcon())
        self.record_button.setText("Parar")
        self.assistant.start_recording()

    def stop_recording(self):
        self.recording = False
        if hasattr(self, "record_action"):
            self.record_action.setText("Iniciar grabacion")
        self.record_button.setText("Grabar")
        self.assistant.stop_recording_and_transcribe()

    def _on_transcription_result(self, text: str):
        self.text_received.emit(text)

    def _on_llm_result(self, text: str):
        self.llm_received.emit(text)

    def _on_status_change(self, msg: str):
        self.status_changed.emit(msg)

    def _set_transcription_safe(self, text: str):
        self.transcription_text.setPlainText(text)
        scrollbar = self.transcription_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _set_status_safe(self, msg: str):
        self.status_label.setText(f"Estado: {msg}")
        if msg.startswith("No se pudo") or msg.startswith("Error"):
            self._set_warning(msg)

    def _set_llm_safe(self, text: str):
        self.llm_text.setPlainText(text)
        scrollbar = self.llm_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._update_llm_height()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Space and event.modifiers() & Qt.ControlModifier:
            self.toggle_recording()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.assistant.cleanup()
        self.tray_icon.hide()
        if hasattr(self, "hotkeys"):
            self.hotkeys.stop()
        QApplication.quit()

    def quit_app(self):
        self.assistant.cleanup()
        self.tray_icon.hide()
        QApplication.quit()

    def _build_device_menus(self):
        self.mic_menu.clear()
        self.sys_menu.clear()
        self.mic_combo.blockSignals(True)
        self.sys_combo.blockSignals(True)
        try:
            self.mic_combo.currentIndexChanged.disconnect()
        except TypeError:
            pass
        try:
            self.sys_combo.currentIndexChanged.disconnect()
        except TypeError:
            pass
        self.mic_combo.clear()
        self.sys_combo.clear()
        self.mic_devices = []
        self.sys_devices = []

        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        
        # Llenar Microfono con sounddevice (como antes)
        for i, info in enumerate(devices):
            name = info.get("name", "Desconocido")
            api = hostapis[info.get("hostapi", 0)].get("name", "?")
            label = f"{i}: {name} ({api})"
            if info.get("max_input_channels", 0) > 0:
                action = QAction(label, self)
                action.triggered.connect(lambda checked, idx=i: self.set_mic_device(idx))
                self.mic_menu.addAction(action)
                self.mic_combo.addItem(f"Microfono: {name} ({api})")
                self.mic_devices.append(i)

        # Llenar Sistema con soundcard (salidas fisicas)
        speakers = sc.all_speakers()
        for i, s in enumerate(speakers):
            label = f"Salida: {s.name}"
            action = QAction(label, self)
            action.triggered.connect(lambda checked, idx=i: self.set_sys_device(idx))
            self.sys_menu.addAction(action)
            self.sys_combo.addItem(label)
            self.sys_devices.append(i)

        self.mic_combo.currentIndexChanged.connect(self._on_mic_combo_changed)
        self.sys_combo.currentIndexChanged.connect(self._on_sys_combo_changed)
        self.mic_combo.blockSignals(False)
        self.sys_combo.blockSignals(False)
        self._update_device_tooltips()
        self._sync_device_selection()
        self._update_capture_mode_warning()

    def _update_loopback_status(self):
        soporta = self.assistant.supports_system_loopback()
        estado = "SI" if soporta else "NO"
        if hasattr(self, "loopback_action"):
            self.loopback_action.setText(f"Loopback soportado: {estado}")

    def set_mic_device(self, device_index: int):
        self.assistant.set_devices(device_index, self.assistant.transcriber.system_device_index)
        self._set_status_safe(f"Microfono: {device_index}")
        self.settings["mic_device_index"] = device_index
        self._save_settings()
        self._sync_device_selection()
        self._update_capture_mode_warning()

    def set_sys_device(self, device_index: int):
        self.assistant.set_devices(self.assistant.transcriber.mic_device_index, device_index)
        self._set_status_safe(f"Sistema: {device_index}")
        self.settings["system_device_index"] = device_index
        self._save_settings()
        self._sync_device_selection()
        self._update_capture_mode_warning()

    def toggle_mic_mode(self):
        if self.assistant.transcriber.mic_mode == "auto":
            self.assistant.set_mic_settings(
                mic_mode="manual",
                mic_energy_threshold=120,
                mic_dynamic=False,
                mic_adjust_duration=0.0,
            )
            if hasattr(self, "mic_mode_action"):
                self.mic_mode_action.setText("Modo microfono: Manual")
            self._set_status_safe("Modo microfono manual")
            self.settings["mic_mode"] = "manual"
            self._save_settings()
        else:
            self.assistant.set_mic_settings(
                mic_mode="auto",
                mic_energy_threshold=150,
                mic_dynamic=True,
                mic_adjust_duration=0.8,
            )
            if hasattr(self, "mic_mode_action"):
                self.mic_mode_action.setText("Modo microfono: Auto")
            self._set_status_safe("Modo microfono auto")
            self.settings["mic_mode"] = "auto"
            self._save_settings()

    def init_hotkeys(self):
        def on_activate():
            self.assistant.send_buffer_to_llm()

        def on_toggle_record():
            self.toggle_recording()

        def on_toggle_collapse():
            self.toggle_collapsed()

        self.hotkeys = keyboard.GlobalHotKeys({
            "<alt_gr>+\\": on_activate,
            "<alt_gr>+g": on_toggle_record,
            "<alt_gr>+h": on_toggle_collapse,
        })
        self.hotkeys.start()

    def move_to_top_center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        w = self.width()
        margin = 20
        x = int((screen.width() - w) / 2)
        self.move(x, margin)

    def _apply_window_size(self):
        screen = QApplication.primaryScreen().availableGeometry()
        max_width = int(screen.width() * 0.40)  # Reducido al 40%
        width = min(480, max_width)            # Maximo 480px de ancho
        self.setFixedWidth(width)
        self.adjustSize()

    def set_position_mode(self, mode):
        self.position_mode = mode
        self.settings["position_mode"] = mode
        self._save_settings()
        self.update_position()

    def update_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        w = self.width()
        margin = 20

        if self.position_mode == "left":
            x = margin
        elif self.position_mode == "right":
            x = screen.width() - w - margin
        else: # center
            x = int((screen.width() - w) / 2)

        self.move(x, margin)

    def toggle_capture_visibility(self):
        self.capture_visible = not self.capture_visible
        self.settings["capture_visible"] = self.capture_visible
        self._save_settings()
        self._apply_capture_affinity()
        self._update_capture_button()

    def _apply_capture_affinity(self):
        if sys.platform != "win32":
            return
        user32 = ctypes.windll.user32
        WDA_NONE = 0x00000000
        WDA_EXCLUDEFROMCAPTURE = 0x00000011
        hwnd = int(self.winId())
        affinity = WDA_NONE if self.capture_visible else WDA_EXCLUDEFROMCAPTURE
        result = user32.SetWindowDisplayAffinity(hwnd, affinity)
        if not result:
            print("No se pudo aplicar la propiedad de exclusión de captura.")

    def _update_capture_button(self):
        if hasattr(self, "capture_button"):
            if self.capture_visible:
                self.capture_button.setIcon(self._icon("eye"))
                self.capture_button.setIconSize(QSize(14, 14))
                self.capture_button.setToolTip("Visible en captura")
            else:
                self.capture_button.setIcon(self._icon("eye_off"))
                self.capture_button.setIconSize(QSize(14, 14))
                self.capture_button.setToolTip("Oculto en captura")

    def toggle_collapsed(self):
        self.is_collapsed = not self.is_collapsed
        self.container.setVisible(not self.is_collapsed)
        if self.is_collapsed:
            self.edge_button.setIcon(self._icon("expand"))
            self.edge_button.setIconSize(QSize(14, 14))
            self.edge_button.setToolTip("Expandir")
        else:
            self.edge_button.setIcon(self._icon("collapse"))
            self.edge_button.setIconSize(QSize(14, 14))
            self.edge_button.setToolTip("Retractar")
        self.settings["collapsed"] = self.is_collapsed
        self._save_settings()
        self.adjustSize()

    def _apply_global_opacity(self, value):
        self.opacity = value
        self.settings["overlay_opacity"] = value
        self._save_settings()
        self.setWindowOpacity(value / 100.0)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if clicked on drag_handle or header_row area (simplified: drag_handle + button row)
            # Actually, let's just make the top part (header_row + control_row) draggable
            if event.pos().y() < 80: # Rough approximation of header height
                 self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                 event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if not self._drag_pos.isNull():
                self.move(event.globalPos() - self._drag_pos)
                event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)

    def cambiar_tema_interfaz(self, nombre_tema):
        self.settings["tema"] = nombre_tema
        self._save_settings()
        self._apply_styles(nombre_tema)

    def cambiar_tema_interfaz(self, nombre_tema):
        self.settings["tema"] = nombre_tema
        self._save_settings()
        self._apply_styles(nombre_tema)
        
        # Actualizar otras ventanas
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "cambiar_tema_interfaz") and widget != self:
                widget.cambiar_tema_interfaz(nombre_tema)

    def _apply_styles(self, tema_nombre="Slate Minimalist"):
        self.setStyleSheet(obtener_qss(tema_nombre))

    def _update_device_tooltips(self):
        self.mic_combo.setToolTip(self.mic_combo.currentText())
        self.sys_combo.setToolTip(self.sys_combo.currentText())

    def _on_mic_combo_changed(self, index):
        if index < 0 or index >= len(self.mic_devices):
            return
        self.mic_combo.setToolTip(self.mic_combo.currentText())
        self.set_mic_device(self.mic_devices[index])

    def _on_sys_combo_changed(self, index):
        if index < 0 or index >= len(self.sys_devices):
            return
        self.sys_combo.setToolTip(self.sys_combo.currentText())
        self.set_sys_device(self.sys_devices[index])

    def _sync_device_selection(self):
        mic_index = self.assistant.transcriber.mic_device_index
        sys_index = self.assistant.transcriber.system_device_index
        if mic_index in self.mic_devices:
            self.mic_combo.blockSignals(True)
            self.mic_combo.setCurrentIndex(self.mic_devices.index(mic_index))
            self.mic_combo.blockSignals(False)
        if sys_index in self.sys_devices:
            self.sys_combo.blockSignals(True)
            self.sys_combo.setCurrentIndex(self.sys_devices.index(sys_index))
            self.sys_combo.blockSignals(False)

    def _config_path(self):
        return writable_config_path("ui_settings.json")

    def _load_settings(self):
        path = self._config_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_settings(self):
        path = self._config_path()
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.settings, handle, indent=2)
        except OSError:
            pass

    def _get_config_path(self, filename="config.json"):
        return writable_config_path(filename)

    def _on_ai_provider_changed(self, index):
        provider = self.ai_provider_combo.currentText()
        if provider == "Local (llama.cpp)":
            self.api_key_input.setVisible(False)
            self.model_id_input.setPlaceholderText("Ruta al modelo .gguf")
            self.browse_model_btn.setVisible(True)
            model_id = self.model_id_input.text().strip()
            if model_id:
                model_path = Path(model_id)
                if not model_path.is_absolute():
                    from app.utils.path_utils import resource_path
                    model_path = Path(resource_path(model_id))
                self.download_model_btn.setVisible(not model_path.exists())
            else:
                self.download_model_btn.setVisible(True)
        else:
            self.api_key_input.setVisible(True)
            self.browse_model_btn.setVisible(False)
            self.download_model_btn.setVisible(False)
            if provider == "Groq":
                self.model_id_input.setPlaceholderText("Opcional: openai/gpt-oss-120b")
            elif provider == "Google":
                self.model_id_input.setPlaceholderText("gemini-2.0-flash")
            else:
                self.model_id_input.setPlaceholderText("ID del modelo")

    def _load_ai_settings(self):
        path = self._get_config_path()
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as handle:
                ai_settings = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return

        # Normalize: "Local" in config → "Local (llama.cpp)" in UI combo
        provider_raw = ai_settings.get("provider", "LM Studio")
        provider = "Local (llama.cpp)" if provider_raw == "Local" else provider_raw
        api_key = ai_settings.get("api_key", "")
        model_id = ai_settings.get("model_id", "")

        self.ai_provider_combo.setCurrentText(provider)
        self.api_key_input.setText(api_key)
        self.model_id_input.setText(model_id)

        if provider == "Local (llama.cpp)":
            self.api_key_input.setVisible(False)
            self.model_id_input.setPlaceholderText("Ruta al modelo .gguf")
            self.browse_model_btn.setVisible(True)
        else:
            self.api_key_input.setVisible(True)
            self.browse_model_btn.setVisible(False)

    def _save_ai_settings(self):
        path = self._get_config_path()
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)

        provider = self.ai_provider_combo.currentText()
        api_key = self.api_key_input.text()
        model_id = self.model_id_input.text().strip()

        # Normalize: "Local (llama.cpp)" in UI → "Local" in config
        if provider == "Local (llama.cpp)":
            provider = "Local"
        if provider == "Google" and not model_id:
            model_id = "gemini-2.0-flash"
        if provider == "Groq" and not model_id:
            model_id = "openai/gpt-oss-120b"

        ai_settings = {
            "provider": provider,
            "api_key": api_key,
            "model_id": model_id,
        }

        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(ai_settings, handle, indent=2)
            self.ai_status_label.setText("Guardado!")
            # Reload the LLM client with the new settings
            get_llm_client().reload()
        except OSError:
            self.ai_status_label.setText("Error!")

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar modelo GGUF", "", "Modelos GGUF (*.gguf)"
        )
        if path:
            self.model_id_input.setText(path)

    def _download_model(self):
        self.download_model_btn.setEnabled(False)
        self.download_model_btn.setText("Descargando...")
        self.ai_status_label.setText("Descargando modelo (769 MB)...")
        QApplication.processEvents()

        from huggingface_hub import hf_hub_download

        if getattr(sys, 'frozen', False):
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            model_dir = base / "AYUDIN" / "models"
        else:
            model_dir = Path(__file__).resolve().parent.parent.parent / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        dest = model_dir / "gemma-3-1b-it-Q4_K_M.gguf"

        try:
            hf_hub_download(
                repo_id="google/gemma-3-1b-it-GGUF",
                filename="gemma-3-1b-it-Q4_K_M.gguf",
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
                resume=True,
            )
            self.ai_status_label.setText("Descarga completada!")
            self.model_id_input.setText(str(dest))
            self.download_model_btn.setVisible(False)
        except Exception as e:
            self.ai_status_label.setText(f"Error: {e}")
        finally:
            self.download_model_btn.setEnabled(True)
            self.download_model_btn.setText("Descargar modelo")

    def toggle_llm_config(self):
        self.llm_config_collapsed = not self.llm_config_collapsed
        self.settings["llm_config_collapsed"] = self.llm_config_collapsed
        self._save_settings()
        self._apply_llm_config_visibility()

    def _apply_llm_config_visibility(self):
        if hasattr(self, "ai_config_body"):
            self.ai_config_body.setVisible(not self.llm_config_collapsed)
        if hasattr(self, "llm_toggle_button"):
            self.llm_toggle_button.setIcon(self._icon("expand") if self.llm_config_collapsed else self._icon("collapse"))
        self.adjustSize()


    def _apply_settings(self):
        mic_index = self.settings.get("mic_device_index")
        sys_index = self.settings.get("system_device_index")
        collapsed = self.settings.get("collapsed", False)
        mic_mode = self.settings.get("mic_mode")
        capture_mode = self.settings.get("capture_mode", "both")
        if mic_index is not None:
            self.assistant.set_devices(mic_index, self.assistant.transcriber.system_device_index)
        if sys_index is not None:
            self.assistant.set_devices(self.assistant.transcriber.mic_device_index, sys_index)
        if mic_mode == "manual":
            self.assistant.set_mic_settings(
                mic_mode="manual",
                mic_energy_threshold=120,
                mic_dynamic=False,
                mic_adjust_duration=0.0,
            )
            if hasattr(self, "mic_mode_action"):
                self.mic_mode_action.setText("Modo microfono: Manual")
        elif mic_mode == "auto":
            self.assistant.set_mic_settings(
                mic_mode="auto",
                mic_energy_threshold=150,
                mic_dynamic=True,
                mic_adjust_duration=0.8,
            )
            if hasattr(self, "mic_mode_action"):
                self.mic_mode_action.setText("Modo microfono: Auto")
        if collapsed:
            self.is_collapsed = True
            self.container.setVisible(False)
            self.edge_button.setIcon(self._icon("expand"))
            self.edge_button.setIconSize(QSize(14, 14))
            self.edge_button.setToolTip("Expandir")
            
        if "position_mode" in self.settings:
            self.position_mode = self.settings["position_mode"]

        self.capture_visible = bool(self.settings.get("capture_visible", False))
        self._update_capture_button()
        self._apply_capture_affinity()

        self.capture_mode = capture_mode
        self.assistant.set_capture_mode(self.capture_mode)
        self._set_capture_mode_ui(self.capture_mode)
        self._update_capture_mode_warning()
            
        self.show()
        self.adjustSize()
        self.update_position()
        self._sync_device_selection()

    def set_capture_mode(self, mode: str):
        if mode not in ("mic", "system", "both"):
            return
        self.capture_mode = mode
        self.settings["capture_mode"] = mode
        self._save_settings()
        self.assistant.set_capture_mode(mode)
        self._set_capture_mode_ui(mode)
        self._update_capture_mode_warning()

    def _set_capture_mode_ui(self, mode: str):
        if hasattr(self, "capture_mic_btn"):
            self.capture_mic_btn.setChecked(mode == "mic")
        if hasattr(self, "capture_sys_btn"):
            self.capture_sys_btn.setChecked(mode == "system")
        if hasattr(self, "capture_both_btn"):
            self.capture_both_btn.setChecked(mode == "both")
        if hasattr(self, "capture_mode_mic_action"):
            self.capture_mode_mic_action.setChecked(mode == "mic")
        if hasattr(self, "capture_mode_sys_action"):
            self.capture_mode_sys_action.setChecked(mode == "system")
        if hasattr(self, "capture_mode_both_action"):
            self.capture_mode_both_action.setChecked(mode == "both")

    def _set_warning(self, message: str):
        if not message:
            self.warning_label.setVisible(False)
            self.warning_label.setText("")
            return
        texto = message if message.startswith("Advertencia") else f"Advertencia: {message}"
        self.warning_label.setText(texto)
        self.warning_label.setVisible(True)

    def _system_audio_available(self) -> bool:
        try:
            return len(sc.all_speakers()) > 0
        except Exception:
            return False

    def _mic_available(self) -> bool:
        try:
            devices = sd.query_devices()
        except Exception:
            return False
        for info in devices:
            if info.get("max_input_channels", 0) > 0:
                return True
        return False

    def _update_capture_mode_warning(self):
        if self.capture_mode == "mic":
            if not self._mic_available():
                self._set_warning("Microfono no disponible")
            else:
                self._set_warning("")
            return

        if self.capture_mode == "system":
            if not self._system_audio_available():
                self._set_warning("Audio del equipo no disponible")
            else:
                self._set_warning("")
            return

        if self.capture_mode == "both":
            mic_ok = self._mic_available()
            sys_ok = self._system_audio_available()
            if not mic_ok and not sys_ok:
                self._set_warning("Microfono y audio del equipo no disponibles")
            elif not mic_ok:
                self._set_warning("Microfono no disponible")
            elif not sys_ok:
                self._set_warning("Audio del equipo no disponible")
            else:
                self._set_warning("")

    def _update_llm_height(self):
        if not hasattr(self, "llm_text"):
            return
        doc_height = int(self.llm_text.document().size().height())
        padding = self.llm_text.frameWidth() * 2 + 12
        desired = doc_height + padding
        if desired < self._llm_min_height:
            desired = self._llm_min_height
        if desired > self._llm_max_height:
            desired = self._llm_max_height
        self.llm_text.setFixedHeight(desired)
        self.adjustSize()
        self.update_position()

    def _mode_icon(self, text: str, color: QColor) -> QIcon:
        return self._text_icon(text, color)

    def _text_icon(self, text: str, color: QColor) -> QIcon:
        size = 16
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(color)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)

    def _icon(self, name: str) -> QIcon:
        path = self._asset_path(os.path.join("icons", f"{name}.svg"))
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()

    def _asset_path(self, relative: str) -> str:
        return asset_path(relative)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverlayWindow()
    sys.exit(app.exec_())
