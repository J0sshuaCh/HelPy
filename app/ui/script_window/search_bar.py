"""
Widget de búsqueda para el visor de guiones.
Permite buscar texto dentro del documento cargado.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QSize
from app.ui.shared import get_icon


class SearchBar(QWidget):
    """Barra de búsqueda para documentos de texto."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_text_edit = None
        self._current_match = 0
        self._total_matches = 0
        
        self._init_ui()
        self.setVisible(False)
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Buscar...")
        self.search_input.setObjectName("deviceCombo")
        self.search_input.returnPressed.connect(self._find_next)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input, 1)
        
        self.match_label = QLabel("0/0", self)
        self.match_label.setObjectName("statusLabel")
        self.match_label.setMinimumWidth(40)
        layout.addWidget(self.match_label)
        
        self.prev_btn = QPushButton("", self)
        self.prev_btn.setObjectName("edgeButton")
        self.prev_btn.setIcon(get_icon("arrow_left"))
        self.prev_btn.setIconSize(QSize(14, 14))
        self.prev_btn.setToolTip("Resultado anterior (Shift+Enter)")
        self.prev_btn.clicked.connect(self._find_prev)
        layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("", self)
        self.next_btn.setObjectName("edgeButton")
        self.next_btn.setIcon(get_icon("arrow_right"))
        self.next_btn.setIconSize(QSize(14, 14))
        self.next_btn.setToolTip("Siguiente resultado (Enter)")
        self.next_btn.clicked.connect(self._find_next)
        layout.addWidget(self.next_btn)
        
        self.close_btn = QPushButton("", self)
        self.close_btn.setObjectName("edgeButton")
        self.close_btn.setIcon(get_icon("eye_off"))
        self.close_btn.setIconSize(QSize(14, 14))
        self.close_btn.setToolTip("Cerrar búsqueda (Escape)")
        self.close_btn.clicked.connect(self.hide_bar)
        layout.addWidget(self.close_btn)
    
    def set_target(self, text_edit):
        """Establece el QTextEdit donde se buscará."""
        self._target_text_edit = text_edit
    
    def toggle(self):
        """Muestra/oculta la barra de búsqueda."""
        if self.isVisible():
            self.hide_bar()
        else:
            self.show_bar()
    
    def show_bar(self):
        self.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def hide_bar(self):
        self.setVisible(False)
        self._clear_highlights()
        if self._target_text_edit:
            self._target_text_edit.setFocus()
    
    def _on_text_changed(self, text):
        self._find_all()
    
    def _find_all(self):
        """Busca todas las ocurrencias del texto."""
        if not self._target_text_edit:
            return
        
        search_text = self.search_input.text()
        if not search_text:
            self._clear_highlights()
            self.match_label.setText("0/0")
            self._total_matches = 0
            self._current_match = 0
            return
        
        # Buscar todas las ocurrencias
        text_content = self._target_text_edit.toPlainText()
        text_lower = text_content.lower()
        search_lower = search_text.lower()
        
        positions = []
        start = 0
        while True:
            pos = text_lower.find(search_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        self._total_matches = len(positions)
        self._current_match = 1 if positions else 0
        self._update_match_label()
        
        # Resaltar el texto actual
        self._highlight_text(search_text)
    
    def _highlight_text(self, search_text):
        """Resalta todas las ocurrencias del texto buscado."""
        if not self._target_text_edit:
            return
        
        from PyQt5.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QColor
        
        document = self._target_text_edit.document()
        cursor = QTextCursor(document)
        
        # Limpiar resaltados anteriores
        cursor.select(QTextCursor.Document)
        fmt = QTextCharFormat()
        cursor.setCharFormat(fmt)
        
        # Resaltar todas las ocurrencias
        if search_text:
            cursor.movePosition(QTextCursor.Start)
            while True:
                cursor = document.find(search_text, cursor, QTextDocument.FindCaseSensitively)
                if cursor.isNull():
                    break
                fmt = QTextCharFormat()
                fmt.setBackground(QColor(255, 255, 0, 100))
                cursor.mergeCharFormat(fmt)
    
    def _clear_highlights(self):
        """Limpia todos los resaltados."""
        if not self._target_text_edit:
            return
        
        from PyQt5.QtGui import QTextCursor, QTextCharFormat
        
        cursor = QTextCursor(self._target_text_edit.document())
        cursor.select(QTextCursor.Document)
        fmt = QTextCharFormat()
        cursor.setCharFormat(fmt)
    
    def _find_next(self):
        """Busca la siguiente ocurrencia."""
        if not self._target_text_edit or not self.search_input.text():
            return
        
        text = self.search_input.text()
        if self._target_text_edit.find(text):
            self._current_match = min(self._current_match + 1, self._total_matches)
        else:
            # Si no encuentra más, volver al inicio
            cursor = self._target_text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self._target_text_edit.setTextCursor(cursor)
            if self._target_text_edit.find(text):
                self._current_match = 1
        
        self._update_match_label()
    
    def _find_prev(self):
        """Busca la ocurrencia anterior."""
        if not self._target_text_edit or not self.search_input.text():
            return
        
        text = self.search_input.text()
        if self._target_text_edit.find(text, QTextCursor.FindBackward):
            self._current_match = max(self._current_match - 1, 1)
        else:
            # Si no encuentra más, ir al final
            cursor = self._target_text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self._target_text_edit.setTextCursor(cursor)
            if self._target_text_edit.find(text, QTextCursor.FindBackward):
                self._current_match = self._total_matches
        
        self._update_match_label()
    
    def _update_match_label(self):
        """Actualiza el label de coincidencias."""
        if self._total_matches > 0:
            self.match_label.setText(f"{self._current_match}/{self._total_matches}")
        else:
            self.match_label.setText("0/0")
    
    def keyPressEvent(self, event):
        """Maneja teclas en la barra de búsqueda."""
        if event.key() == Qt.Key_Escape:
            self.hide_bar()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                self._find_prev()
            else:
                self._find_next()
        else:
            super().keyPressEvent(event)
