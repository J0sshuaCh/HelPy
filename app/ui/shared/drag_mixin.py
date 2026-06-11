from PyQt5.QtCore import Qt, QPoint

class DragMixin:
    """
    A mixin that allows a window to be dragged when clicking on its top area.
    Expects the class to be a QWidget subclass.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_pos = QPoint()
        self._drag_threshold_y = 80  # Rough approximation of header height

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().y() < self._drag_threshold_y:
                 self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                 event.accept()
        # Only call super if we haven't intercepted it, or call it anyway?
        # Typically good to call super to let child widgets handle clicks if missed
        if hasattr(super(), 'mousePressEvent'):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if not self._drag_pos.isNull():
                self.move(event.globalPos() - self._drag_pos)
                event.accept()
        if hasattr(super(), 'mouseMoveEvent'):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        if hasattr(super(), 'mouseReleaseEvent'):
            super().mouseReleaseEvent(event)
