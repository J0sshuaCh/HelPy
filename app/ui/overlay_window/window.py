import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QApplication, QLabel, QMessageBox, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize

from app.core.assistant_controller import AssistantController
from app.ui.shared import ui_settings, DragMixin, apply_capture_affinity, update_window_position, apply_window_size, get_icon, LoadingSpinner, SpinnerOverlay
from app.ui.shared.animations import AnimatedCollapseMixin
from app.utils.logger import get_logger

logger = get_logger(__name__)

from .ui import HeaderArea, PositionBar, CapturePanel, RecordingPanel, TextDisplayPanel, ContextPanel
from .device_manager import DeviceManager
from .theme_manager import ThemeManager
from .preferences_dialog import PreferencesDialog
from .tray import TrayManager
from .hotkeys import HotkeyManager

class OverlayWindow(AnimatedCollapseMixin, DragMixin, QWidget):
    text_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    llm_received = pyqtSignal(str)
    llm_chunk_received = pyqtSignal(str)
    llm_error_received = pyqtSignal(str)
    llm_busy_changed = pyqtSignal(bool)
    overlay_requested = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # State
        self.recording = False
        self.is_collapsed = ui_settings.get("collapsed", False)
        self.position_mode = ui_settings.get("position_mode", "right")
        self.capture_visible = ui_settings.get("capture_visible", False)
        self.opacity = ui_settings.get("overlay_opacity", 100)
        self.capture_mode = ui_settings.get("capture_mode", "both")
        self.compact_mode = ui_settings.get("compact_mode", False)

        from PyQt5.QtGui import QIcon
        from app.ui.shared.icons import get_logo_pixmap
        self.setWindowIcon(QIcon(get_logo_pixmap(64, 64)))
        
        import json
        from app.utils.path_utils import writable_config_path
        stt_provider = "google"
        whisper_model = "tiny"
        try:
            with open(writable_config_path("config.json"), "r", encoding="utf-8") as f:
                cfg = json.load(f)
                stt_provider = cfg.get("stt_provider", "google")
                whisper_model = cfg.get("whisper_model", "tiny")
        except Exception:
            logger.exception("Error al leer config.json; se usan valores por defecto")

        # Core Assistant
        self.assistant = AssistantController(
            stt_provider=stt_provider,
            whisper_model=whisper_model,
            mic_device_index=ui_settings.get("mic_device_index"),
            system_device_index=ui_settings.get("system_device_index"),
            capture_mode=self.capture_mode,
        )
        self.assistant.on_result(self._on_transcription_result)
        self.assistant.on_status(self._on_status_change)
        self.assistant.on_llm_result(self._on_llm_result)
        self.assistant.on_llm_chunk(self._on_llm_chunk)
        self.assistant.on_llm_error(self._on_llm_error)
        self.assistant.on_audio_level(self._on_audio_level)
        self.assistant.on_llm_busy(self._on_llm_busy)

        # Signals
        self.text_received.connect(self._set_transcription_safe)
        self.status_changed.connect(self._set_status_safe)
        self.llm_received.connect(self._set_llm_safe)
        self.llm_chunk_received.connect(self._set_llm_chunk_safe)
        self.llm_error_received.connect(self._set_llm_error_safe)
        self.llm_busy_changed.connect(self._set_llm_busy_safe)
        self.overlay_requested.connect(self._set_overlay_safe)

        self._init_ui()
        
        # Managers
        self.theme_manager = ThemeManager(ui_settings, self)
        self.device_manager = DeviceManager(self.assistant, self.capture_panel, ui_settings, self)
        
        # Preferencias (config fuera del overlay always-on-top)
        self.preferences_dialog = PreferencesDialog(ui_settings, self.theme_manager, self)

        # Tray and Hotkeys
        self.tray_manager = TrayManager(self, self.assistant, self.device_manager)
        self.hotkey_manager = HotkeyManager(self)
        self.hotkey_manager.register_on_change(self.recording_panel.refresh_hotkey_tooltips)
        self.hotkey_manager.register_on_change(self.header_area.refresh_hotkey_tooltips)
        # Refresca los tooltips por si el fallback de inicio descartó atajos inválidos
        self.recording_panel.refresh_hotkey_tooltips()
        self.header_area.refresh_hotkey_tooltips()
        
        self._apply_settings()
        
        # Validación de configuración al inicio
        self._run_startup_validation()
        
        # Mostrar onboarding en primer lanzamiento
        self._show_onboarding_if_needed()
        
        # Initial refresh
        self.device_manager.refresh()
        apply_window_size(self, max_width_ratio=0.45, max_pixels=640)
        
        self.show()
        self.adjustSize()
        self.update_position()
        self.position_bar.set_active_position(self.position_mode)
        self._apply_capture_affinity()

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # UI Components
        self.header_area = HeaderArea(parent=self)
        self.header_area.capture_button.clicked.connect(self.toggle_capture_visibility)
        self.header_area.compact_button.clicked.connect(self.toggle_compact_mode)
        self.header_area.settings_button.clicked.connect(self.open_preferences)
        self.header_area.edge_button.clicked.connect(self.toggle_collapsed)
        self.main_layout.addWidget(self.header_area)

        self.container = QFrame(self)
        self.container.setObjectName("overlayContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 5, 16, 16)
        self.container_layout.setSpacing(10)
        
        self.position_bar = PositionBar(ui_settings, initial_opacity=self.opacity, parent=self)
        self.position_bar.pos_left_btn.clicked.connect(lambda: self.set_position_mode("left"))
        self.position_bar.pos_center_btn.clicked.connect(lambda: self.set_position_mode("center"))
        self.position_bar.pos_right_btn.clicked.connect(lambda: self.set_position_mode("right"))
        self.position_bar.opacity_slider.valueChanged.connect(self._apply_global_opacity)
        self.container_layout.addWidget(self.position_bar)
        
        self.capture_panel = CapturePanel(ui_settings, self)
        self.capture_panel.capture_mic_btn.clicked.connect(lambda: self.set_capture_mode("mic"))
        self.capture_panel.capture_sys_btn.clicked.connect(lambda: self.set_capture_mode("system"))
        self.capture_panel.capture_both_btn.clicked.connect(lambda: self.set_capture_mode("both"))
        self.capture_panel.refresh_button.clicked.connect(lambda: self.device_manager.refresh())
        self.container_layout.addWidget(self.capture_panel)
        
        self.recording_panel = RecordingPanel(self)
        self.recording_panel.record_button.clicked.connect(self.toggle_recording)
        self.recording_panel.send_button.clicked.connect(self._on_send_clicked)
        self.container_layout.addWidget(self.recording_panel)
        
        self.context_panel = ContextPanel(ui_settings, self)
        self.container_layout.addWidget(self.context_panel)
        
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(6)
        self.status_spinner = LoadingSpinner(self, size=14, line_width=2, speed=40)
        status_row.addWidget(self.status_spinner)
        self.status_label = QLabel("Estado: listo", self)
        self.status_label.setObjectName("statusLabel")
        status_row.addWidget(self.status_label, 1)
        self.container_layout.addLayout(status_row)

        self._last_status_msg = "listo"
        self._send_available = False
        self._update_send_button_state()

        self.warning_row = QHBoxLayout()
        self.warning_row.setContentsMargins(0, 0, 0, 0)
        self.warning_row.setSpacing(4)
        self.warning_label = QLabel("", self)
        self.warning_label.setObjectName("warningLabel")
        self.warning_label.setVisible(False)
        self.warning_dismiss_btn = QPushButton("", self)
        self.warning_dismiss_btn.setObjectName("edgeButton")
        self.warning_dismiss_btn.setIcon(get_icon("close"))
        self.warning_dismiss_btn.setIconSize(QSize(12, 12))
        self.warning_dismiss_btn.setToolTip("Descartar el aviso")
        self.warning_dismiss_btn.setVisible(False)
        self.warning_dismiss_btn.clicked.connect(self._clear_banner)
        self.warning_row.addWidget(self.warning_label, 1)
        self.warning_row.addWidget(self.warning_dismiss_btn, 0)
        self.container_layout.addLayout(self.warning_row)

        self.overlay = SpinnerOverlay(self.container, spinner_size=48)
        self.overlay.hide()
        
        # Text display added at the end
        self.text_display = TextDisplayPanel(self)
        self.container_layout.addWidget(self.text_display)
        self.text_display.llm_text.document().contentsChanged.connect(self._update_llm_height)
        
        self.main_layout.addWidget(self.container)

        self._setup_collapse_animation(self.container, self.header_area.edge_button, duration=300)

    def _apply_settings(self):
        mic_mode = ui_settings.get("mic_mode")
        if mic_mode == "manual":
            self.assistant.set_mic_settings(mic_mode="manual", mic_energy_threshold=120, mic_dynamic=False, mic_adjust_duration=0.0)
            self.tray_manager.update_mic_mode("manual")
        elif mic_mode == "auto":
            self.assistant.set_mic_settings(mic_mode="auto", mic_energy_threshold=150, mic_dynamic=True, mic_adjust_duration=0.8)
            self.tray_manager.update_mic_mode("auto")

        if self.is_collapsed:
            self.container.setVisible(False)
            self.header_area.edge_button.setIcon(get_icon("expand"))
            self.header_area.edge_button.setToolTip("Expandir")
            
        self._update_capture_button()
        self._apply_capture_affinity()
        self._apply_compact_mode()
        
        self.assistant.set_capture_mode(self.capture_mode)
        self._set_capture_mode_ui(self.capture_mode)
        self._update_capture_mode_warning()
        self.setWindowOpacity(self.opacity / 100.0)

    def reload_icons(self):
        self._update_capture_button()
        self.header_area.refresh_icons()
        self.header_area.compact_button.setChecked(self.compact_mode)
        self.position_bar.reload_icons()
        self.capture_panel.reload_icons()
        self.recording_panel.refresh_hotkey_tooltips()
        self.header_area.refresh_hotkey_tooltips()
        if hasattr(self, "preferences_dialog"):
            self.preferences_dialog.reload_icons()

    # --- Actions ---
    def open_preferences(self):
        self.preferences_dialog.show_preferences()

    def toggle_recording(self):
        if self.recording:
            self.recording = False
            self.header_area.set_recording(False)
            self.tray_manager.update_recording_state(False)
            self.recording_panel.record_button.setText("Grabar")
            self.assistant.stop_recording_and_transcribe()
            self.recording_panel.vu_meter.reset()
            self.recording_panel.stop_timer()
            # Al parar se vacía el buffer: el envío deja de estar disponible.
            self._send_available = False
            self._update_send_button_state()
        else:
            started, _ = self.assistant.start_recording()
            if not started:
                # No pasar la UI a "grabando" si el transcriber no arrancó;
                # el assistant ya emitió el fallo y los warnings por el canal de estado.
                return
            self.recording = True
            self.header_area.set_recording(True)
            self.tray_manager.update_recording_state(True)
            self.recording_panel.record_button.setText("Detener")
            self.recording_panel.start_timer()
        if self.compact_mode:
            self._update_recording_strip()
            self.adjustSize()

    def _reset_recording_state(self):
        """Re-sincroniza la UI al estado real del transcriber (p. ej. tras un reinicio fallido)."""
        self.recording = False
        self.header_area.set_recording(False)
        self.tray_manager.update_recording_state(False)
        self.recording_panel.record_button.setText("Grabar")
        self.recording_panel.vu_meter.reset()
        if self.compact_mode:
            self._update_recording_strip()
        self.adjustSize()

    def _on_send_clicked(self):
        if self.assistant.is_llm_busy():
            self.assistant.cancel_llm()
        else:
            self.assistant.send_buffer_to_llm()

    def _on_llm_busy(self, busy: bool):
        self.llm_busy_changed.emit(busy)

    def _set_llm_busy_safe(self, busy: bool):
        self._llm_busy = busy
        if busy:
            self.recording_panel.send_button.setText("Cancelar envío")
            self.recording_panel.send_button.setToolTip("Cancelar el envío en curso")
            self.recording_panel.send_button.setEnabled(True)
        else:
            self.recording_panel.send_button.setText("Enviar a IA")
            self.recording_panel.refresh_hotkey_tooltips()
            self._update_send_button_state()

    def _update_send_button_state(self):
        """Enviar a IA solo queda activo si hay texto en el buffer."""
        available = self._send_available and not getattr(self, "_llm_busy", False)
        self.recording_panel.send_button.setEnabled(available)
        self.recording_panel.set_send_available(available)

    def set_capture_mode(self, mode: str):
        if mode not in ("mic", "system", "both"): return
        self.capture_mode = mode
        ui_settings.set("capture_mode", mode)
        started, was_running = self.assistant.set_capture_mode(mode)
        self._set_capture_mode_ui(mode)
        self._update_capture_mode_warning()
        if self.recording and was_running and not started:
            self._reset_recording_state()

    def set_position_mode(self, mode):
        self.position_mode = mode
        ui_settings.set("position_mode", mode)
        self.position_bar.set_active_position(mode)
        self.update_position()

    def update_position(self):
        update_window_position(self, self.position_mode)

    def toggle_collapsed(self):
        self._animate_toggle_collapsed()
        self.header_area.set_collapsed_tooltip(self.is_collapsed)
        ui_settings.set("collapsed", self.is_collapsed)

    def toggle_capture_visibility(self):
        self.capture_visible = not self.capture_visible
        ui_settings.set("capture_visible", self.capture_visible)
        self._apply_capture_affinity()
        self._update_capture_button()

    def toggle_compact_mode(self):
        """Alterna entre modo expandido (todo visible) y compacto (solo respuesta de la IA)."""
        self.compact_mode = not self.compact_mode
        ui_settings.set("compact_mode", self.compact_mode)
        self._apply_compact_mode()

    def _apply_compact_mode(self):
        """Aplica el modo compacto/expandido."""
        is_compact = self.compact_mode
        
        # Mostrar/ocultar paneles según el modo
        self.capture_panel.setVisible(not is_compact)

        self.context_panel.setVisible(not is_compact)
        self.text_display.transcription_label.setVisible(not is_compact)
        self.text_display.transcription_text.setVisible(not is_compact)

        # En compacto, el panel de grabación queda como franja mínima: el botón
        # Grabar/Detener siempre a la vista y, mientras se graba, VU + Enviar.
        self._update_recording_strip()

        # Compactar el header: en modo compacto solo logo, título, indicador y
        # colapsar son visibles; el resto del chrome se oculta.
        self.header_area.set_compact_header(is_compact)

        # Actualizar icono y estado del botón
        self.header_area.compact_button.setIcon(get_icon("panels"))
        self.header_area.compact_button.setChecked(is_compact)
        self.header_area.compact_button.setToolTip(
            "Modo expandido (mostrar todo)"
            if is_compact
            else "Modo compacto (solo respuesta; la grabación queda a un clic)"
        )
        
        self.adjustSize()

    def _update_recording_strip(self):
        """En compacto: Grabar/Detener siempre visible; VU, temporizador y Enviar solo mientras se graba."""
        is_compact = self.compact_mode
        recording = self.recording
        self.recording_panel.send_button.setVisible(not is_compact or recording)
        self.recording_panel.vu_meter.setVisible(not is_compact or recording)
        self.recording_panel.timer_label.setVisible(recording)

    def toggle_mic_mode(self):
        if self.assistant.transcriber.mic_mode == "auto":
            self.assistant.set_mic_settings(mic_mode="manual", mic_energy_threshold=120, mic_dynamic=False, mic_adjust_duration=0.0)
            self.tray_manager.update_mic_mode("manual")
            self._set_status_safe("Sensibilidad del micrófono: fija")
            ui_settings.set("mic_mode", "manual")
        else:
            self.assistant.set_mic_settings(mic_mode="auto", mic_energy_threshold=150, mic_dynamic=True, mic_adjust_duration=0.8)
            self.tray_manager.update_mic_mode("auto")
            self._set_status_safe("Sensibilidad del micrófono: automática")
            ui_settings.set("mic_mode", "auto")

    def quit_app(self):
        if self.recording and not self._confirm_quit_if_recording():
            return
        self._do_shutdown()

    def _confirm_quit_if_recording(self) -> bool:
        reply = QMessageBox.question(
            self,
            "¿Salir de HelPy?",
            "Se está grabando en este momento.\n¿Salir de todas formas? Se perderá la transcripción en curso.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _do_shutdown(self):
        self.assistant.cleanup()
        self.tray_manager.hide()
        self.hotkey_manager.stop()
        QApplication.quit()

    # --- UI Helpers ---
    def _run_startup_validation(self):
        """Ejecuta validación de configuración al inicio y muestra advertencias."""
        try:
            from app.core.startup_validator import validate_startup, get_validation_summary
            issues = validate_startup()
            if issues:
                errors = [msg for tipo, msg in issues if tipo == "error"]
                warnings = [msg for tipo, msg in issues if tipo == "warning"]
                
                # Mostrar errores en el status
                if errors:
                    self._set_warning(errors[0], level="error")
                
                # Imprimir resumen completo en consola
                summary = get_validation_summary(issues)
                print(f"\n{'='*50}")
                print("VALIDACIÓN DE INICIO:")
                print(summary)
                print(f"{'='*50}\n")
        except Exception:
            logger.exception("Error en la validación de inicio")
    
    def _show_onboarding_if_needed(self):
        """Muestra el diálogo de onboarding en el primer lanzamiento."""
        if not ui_settings.get("onboarding_completed", False):
            try:
                from app.ui.onboarding_dialog import OnboardingDialog
                from PyQt5.QtCore import QTimer
                # Mostrar después de que la ventana esté visible
                QTimer.singleShot(500, self._show_onboarding)
            except Exception:
                logger.exception("Error al mostrar el onboarding")
    
    def _show_onboarding(self):
        from app.ui.onboarding_dialog import OnboardingDialog
        self._onboarding_dialog = OnboardingDialog(self)
        self._onboarding_dialog.accepted.connect(self._on_onboarding_done)
        self._onboarding_dialog.rejected.connect(self._on_onboarding_done)
        # Evitar que Qt cierre la app al cerrar el único Qt.Window visible
        QApplication.instance().setQuitOnLastWindowClosed(False)
        self._onboarding_dialog.show()

    def _on_onboarding_done(self):
        ui_settings.set("onboarding_completed", True)
        QApplication.instance().setQuitOnLastWindowClosed(True)
        self._onboarding_dialog = None
    
    def _apply_global_opacity(self, value):
        self.opacity = value
        ui_settings.set("overlay_opacity", value)
        self.setWindowOpacity(value / 100.0)
        self.position_bar.opacity_pct_label.setText(f"{value}%")
        self.position_bar.opacity_slider.blockSignals(True)
        self.position_bar.opacity_slider.setValue(value)
        self.position_bar.opacity_slider.blockSignals(False)

    def _apply_capture_affinity(self):
        apply_capture_affinity(int(self.winId()), self.capture_visible)

    def _update_capture_button(self):
        icon_name = "eye" if self.capture_visible else "eye_off"
        self.header_area.capture_button.setIcon(get_icon(icon_name))
        self.header_area.capture_button.setToolTip("Visible en captura" if self.capture_visible else "Oculto en captura")

    def _set_capture_mode_ui(self, mode: str):
        self.capture_panel.capture_mic_btn.setChecked(mode == "mic")
        self.capture_panel.capture_sys_btn.setChecked(mode == "system")
        self.capture_panel.capture_both_btn.setChecked(mode == "both")
        self.capture_panel.apply_mode(mode)

    def _update_capture_mode_warning(self):
        mic_ok = self.device_manager.mic_available()
        sys_ok = self.device_manager.system_audio_available()
        
        if self.capture_mode == "mic" and not mic_ok:
            self._set_warning("Micrófono no disponible. Conecta uno y revisa los dispositivos.")
        elif self.capture_mode == "system" and not sys_ok:
            self._set_warning("Audio del sistema no disponible. Revisa la salida de audio.")
        elif self.capture_mode == "both":
            if not mic_ok and not sys_ok:
                self._set_warning("Micrófono y audio del sistema no disponibles. Revisa tus dispositivos.")
            elif not mic_ok:
                self._set_warning("Micrófono no disponible. Conecta uno y revisa los dispositivos.")
            elif not sys_ok:
                self._set_warning("Audio del sistema no disponible. Revisa la salida de audio.")
            else:
                self._set_warning("")
        else:
            self._set_warning("")

    def _set_warning(self, message: str, level: str = "warning", auto_clear_ms=None):
        if not hasattr(self, "_warning_timer"):
            self._warning_timer = QTimer(self)
            self._warning_timer.setSingleShot(True)
            self._warning_timer.timeout.connect(self._clear_banner)
        self._warning_timer.stop()
        if not message:
            self.warning_label.setProperty("level", "warning")
            self.warning_label.setVisible(False)
            self.warning_dismiss_btn.setVisible(False)
            self.warning_label.setText("")
            return
        prefix = "Error" if level == "error" else "Advertencia"
        texto = message if message.startswith(prefix) else f"{prefix}: {message}"
        self.warning_label.setText(texto)
        self.warning_label.setProperty("level", level)
        self.warning_label.style().unpolish(self.warning_label)
        self.warning_label.style().polish(self.warning_label)
        self.warning_label.setVisible(True)
        self.warning_dismiss_btn.setVisible(True)
        if auto_clear_ms:
            self._warning_timer.start(auto_clear_ms)

    def _clear_banner(self):
        """Limpia el banner y restaura el último status no-error."""
        self._set_warning("")
        self.status_label.setText(f"Estado: {getattr(self, '_last_status_msg', 'listo')}")
        self.status_spinner.stop()

    def _update_llm_height(self):
        doc_height = int(self.text_display.llm_text.document().size().height())
        padding = self.text_display.llm_text.frameWidth() * 2 + 12
        desired = doc_height + padding
        desired = max(self.text_display.llm_min_height, min(desired, self.text_display.llm_max_height))
        self.text_display.llm_text.setFixedHeight(desired)
        self.adjustSize()

    # --- Callbacks ---
    def _on_transcription_result(self, text: str):
        self.text_received.emit(text)

    def _on_llm_result(self, text: str):
        self.llm_received.emit(text)

    def _on_llm_chunk(self, chunk: str):
        self.llm_chunk_received.emit(chunk)

    def _on_llm_error(self, msg: str):
        self.llm_error_received.emit(msg)

    def _on_status_change(self, msg: str):
        self.status_changed.emit(msg)

    def _on_audio_level(self, level: float):
        self.recording_panel.vu_meter.set_level(level)

    def _set_transcription_safe(self, text: str):
        self.text_display.transcription_text.setPlainText(text)
        scrollbar = self.text_display.transcription_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        if text.strip():
            self._send_available = True
            self._update_send_button_state()

    def _set_status_safe(self, msg: str):
        if msg.startswith("Error") or msg.startswith("No se pudo"):
            # El error persiste 30 s para que el usuario lo vea; si es transitorio
            # (red, timeout) se limpia solo. El usuario puede descartarlo antes.
            self._set_warning(msg, level="error", auto_clear_ms=30000)
            self.status_label.setText("Estado: error")
            self.status_spinner.stop()
            return
        self._last_status_msg = msg
        self.status_label.setText(f"Estado: {msg}")

        loading_keywords = [
            "Escuchando", "Procesando audio", "Enviando a la IA",
            "Descargando modelo", "Cargando modelo",
        ]
        if any(kw in msg for kw in loading_keywords):
            self.status_spinner.start()
        else:
            self.status_spinner.stop()

    def _set_overlay_safe(self, visible: bool, text: str):
        if visible:
            self.overlay.show_overlay(text)
        else:
            self.overlay.hide_overlay()

    def _set_llm_chunk_safe(self, chunk: str):
        if not chunk:
            self.text_display.llm_text.clear()
            return
        cursor = self.text_display.llm_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        self.text_display._smart_scroll_to_bottom()

    def _set_llm_safe(self, text: str):
        self.text_display.llm_text.setPlainText(text)
        self.text_display._smart_scroll_to_bottom()
        self._update_llm_height()

    def _set_llm_error_safe(self, msg: str):
        self._set_warning(msg, level="error", auto_clear_ms=30000)

    # --- Events ---
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.toggle_collapsed()
            return
        if event.key() == Qt.Key_Space and event.modifiers() & Qt.ControlModifier:
            self.toggle_recording()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.recording:
            if not self._confirm_quit_if_recording():
                event.ignore()
                return
        self._do_shutdown()
