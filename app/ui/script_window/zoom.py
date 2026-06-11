from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt

class ZoomManager:
    def __init__(self, window, initial_zoom=1.0):
        self.window = window
        self.zoom_factor = initial_zoom

    def handle_wheel_event(self, event, settings):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_factor = min(3.0, self.zoom_factor + 0.1)
        else:
            self.zoom_factor = max(0.5, self.zoom_factor - 0.1)
        
        settings.set("script_zoom", self.zoom_factor)
        
        if self.window.viewer_stack.currentWidget() == self.window.pdf_scroll:
            self.update_pdf_pages_size()
        else:
            self.apply_text_zoom()

    def update_pdf_pages_size(self):
        if self.window.viewer_stack.currentWidget() != self.window.pdf_scroll:
            return
            
        # Target width: container width minus scrollbar and margins
        target_width = int((self.window.container.width() - 45) * self.zoom_factor)
        
        layout = self.window.pdf_scroll.pdf_layout
        for i in range(layout.count()):
            label = layout.itemAt(i).widget()
            if isinstance(label, QLabel):
                orig = label.property("original_pixmap")
                if orig:
                    scaled = orig.scaledToWidth(target_width, Qt.SmoothTransformation)
                    label.setPixmap(scaled)
                    
                # Re-apply effect after scaling if needed
                if not label.graphicsEffect():
                    effect = QGraphicsOpacityEffect(label)
                    effect.setOpacity(1.0)
                    label.setGraphicsEffect(effect)

    def apply_text_zoom(self):
        # Base size is 13px, apply zoom factor
        new_size = max(8, int(13 * self.zoom_factor))
        font = self.window.md_view.font()
        font.setPointSize(new_size)
        self.window.md_view.setFont(font)
