from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtWidgets import (
    QWidget, QApplication, QAbstractButton, QLineEdit, QComboBox,
    QAbstractScrollArea, QSlider,
)


class DragMixin:
    """
    Mixin que permite arrastrar una ventana sin bordes con el ratón.

    Cualquier zona "pasiva" de la ventana (fondo, labels, frames) actúa como
    asa de arrastre. Los controles interactivos (botones, campos de texto,
    áreas de scroll, combos, sliders) conservan su comportamiento normal.

    Funciona tanto sobre la propia ventana como sobre sus hijos (mediante
    un eventFilter instalado en todos los descendientes), por lo que sirve
    para QWidget, QDialog y las ventanas con header/paneles.
    """
    # Tipos de widget que nunca deben iniciar un arrastre de ventana.
    _INTERACTIVE_TYPES = (
        QAbstractButton,
        QLineEdit,
        QComboBox,
        QAbstractScrollArea,
        QSlider,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_pos = QPoint()
        self._drag_target = None   # widget hijo que capturó el arrastre
        self._drag_active = False

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _is_drag_source(self, widget):
        """Un widget es fuente de arrastre si ni él ni sus ancestros
        (hasta esta ventana) son controles interactivos."""
        w = widget
        while w is not None and w is not self:
            if isinstance(w, self._INTERACTIVE_TYPES):
                return False
            w = w.parentWidget()
        return True

    def _install_drag_filters(self):
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

    def _begin_drag(self, global_pos):
        self._drag_pos = global_pos - self.frameGeometry().topLeft()
        self._drag_active = False

    def _update_drag(self, global_pos):
        delta = global_pos - (self._drag_pos + self.frameGeometry().topLeft())
        if not self._drag_active:
            # No mover por un simple clic: requiere superar la distancia mínima.
            if delta.manhattanLength() < QApplication.startDragDistance():
                return
            self._drag_active = True
        self.move(global_pos - self._drag_pos)

    def _end_drag(self):
        self._drag_pos = QPoint()
        self._drag_active = False

    # ------------------------------------------------------------------
    # Arrastre directo sobre el fondo de la ventana
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._begin_drag(event.globalPos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and not self._drag_pos.isNull():
            self._update_drag(event.globalPos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._end_drag()
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------
    # Arrastre sobre widgets hijos (event filter)
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        if isinstance(obj, QWidget) and obj is not self:
            etype = event.type()
            if etype == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if self._is_drag_source(obj):
                    self._drag_target = obj
                    self._begin_drag(event.globalPos())
                    return True  # capturamos el clic para poder arrastrar
            elif etype == QEvent.MouseMove and obj is self._drag_target:
                if event.buttons() & Qt.LeftButton and not self._drag_pos.isNull():
                    self._update_drag(event.globalPos())
                    return True
            elif etype == QEvent.MouseButtonRelease and obj is self._drag_target:
                self._drag_target = None
                self._end_drag()
                return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        self._install_drag_filters()
        super().showEvent(event)
