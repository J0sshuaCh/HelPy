import os
import fitz  # PyMuPDF
from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

class FileLoader:
    def __init__(self, window):
        self.window = window

    def load_script(self, path: str):
        if not path:
            return
        if not os.path.exists(path):
            self.window.path_label.setText(f"No existe: {path}")
            return

        ext = path.lower()
        if ext.endswith((".md", ".markdown")):
            self.load_markdown(path)
        elif ext.endswith(".pdf"):
            self.load_pdf(path)
        elif ext.endswith(".txt"):
            self.load_txt(path)
        else:
            self.window.path_label.setText(f"Formato no soportado: {path}")

    def load_pdf(self, path: str):
        try:
            self._clear_pdf_layout()
            doc = fitz.open(path)
            
            # Use high DPI for base images
            zoom = 2.0 
            mat = fitz.Matrix(zoom, zoom)

            for page in doc:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                fmt = QImage.Format_RGB888
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                
                label = QLabel()
                pixmap = QPixmap.fromImage(img)
                label.setPixmap(pixmap)
                # Store the original pixmap for resizing
                label.setProperty("original_pixmap", pixmap)
                label.setAlignment(Qt.AlignCenter)
                
                # Apply initial opacity effect container
                effect = QGraphicsOpacityEffect(label)
                effect.setOpacity(1.0) # Controlled by window opacity
                label.setGraphicsEffect(effect)
                
                self.window.pdf_scroll.pdf_layout.addWidget(label)
            
            doc.close()
            self.window.viewer_stack.setCurrentWidget(self.window.pdf_scroll)
            self.window.zoom_manager.update_pdf_pages_size()
            self.window._update_after_load(path)
        except Exception as exc:
            self.window.path_label.setText(f"Error PDF: {exc}")

    def _clear_pdf_layout(self):
        layout = self.window.pdf_scroll.pdf_layout
        for i in reversed(range(layout.count())): 
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def load_txt(self, path: str):
        text = self._read_text_file(path)
        if text is not None:
            self.window.md_view.setPlainText(text)
            self.window.zoom_manager.apply_text_zoom()
            self.window.viewer_stack.setCurrentWidget(self.window.md_view)
            self.window._update_after_load(path)

    def load_markdown(self, path: str):
        text = self._read_text_file(path)
        if text is not None:
            self.window.md_view.setMarkdown(text)
            self.window.zoom_manager.apply_text_zoom()
            self.window.viewer_stack.setCurrentWidget(self.window.md_view)
            self.window._update_after_load(path)

    def _read_text_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1", errors="replace") as handle:
                    return handle.read()
            except Exception as exc:
                self.window.path_label.setText(f"Error leyendo: {exc}")
                return None
        except OSError as exc:
            self.window.path_label.setText(f"Error OSError: {exc}")
            return None
