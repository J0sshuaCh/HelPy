import os
import fitz  # PyMuPDF
from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect, QTextEdit, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

class FileLoader:
    def __init__(self, window):
        self.window = window

    def load_script(self, path: str):
        if not path:
            return
        if not os.path.exists(path):
            self._show_error("Archivo no encontrado", f"El archivo no existe:\n{path}")
            return

        ext = path.lower()
        if ext.endswith((".md", ".markdown")):
            self.load_markdown(path)
        elif ext.endswith(".pdf"):
            self.load_pdf(path)
        elif ext.endswith(".txt"):
            self.load_txt(path)
        else:
            self._show_error("Formato no compatible", "Usa archivos .md, .pdf o .txt.")

    def load_pdf(self, path: str):
        try:
            self._clear_pdf_layout()
            self.window._pdf_texts = []
            doc = fitz.open(path)
            
            # Use high DPI for base images
            zoom = 2.0 
            mat = fitz.Matrix(zoom, zoom)

            for page_num, page in enumerate(doc):
                # Extract text for search
                self.window._pdf_texts.append(page.get_text())
                
                pix = page.get_pixmap(matrix=mat, alpha=False)
                fmt = QImage.Format_RGB888
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                
                label = QLabel()
                pixmap = QPixmap.fromImage(img)
                label.setPixmap(pixmap)
                label.setProperty("original_pixmap", pixmap)
                label.setProperty("page_num", page_num)
                label.setAlignment(Qt.AlignCenter)
                
                effect = QGraphicsOpacityEffect(label)
                effect.setOpacity(1.0)
                label.setGraphicsEffect(effect)
                
                self.window.pdf_scroll.pdf_layout.addWidget(label)
            
            doc.close()
            self.window.viewer_stack.setCurrentWidget(self.window.pdf_scroll)
            self.window.zoom_manager.update_pdf_pages_size()
            self.window._update_after_load(path)
        except Exception as exc:
            msg = str(exc).lower()
            if "encrypt" in msg or "password" in msg:
                self._show_error("PDF protegido", "El PDF está cifrado o protegido con contraseña.\nNo se puede abrir.")
            elif "xref" in msg or "no objects" in msg:
                self._show_error("PDF dañado", "El archivo PDF parece estar dañado o incompleto.")
            elif "memory" in msg:
                self._show_error("PDF demasiado grande", "El archivo PDF es demasiado grande para procesarlo.\nIntenta con un archivo más pequeño.")
            elif "permission" in msg or "access" in msg or "errno" in msg:
                self._show_error("Archivo en uso", "No se pudo acceder al archivo.\nVerifica que no esté abierto en otro programa.")
            else:
                self._show_error("Error al abrir PDF", "No se pudo abrir el PDF.\nVerifica que el archivo no esté dañado.")

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
                self._show_error("Error al leer el archivo", str(exc))
                return None
        except OSError as exc:
            self._show_error("Error al leer el archivo", str(exc))
            return None

    @staticmethod
    def _show_error(title: str, detail: str):
        QMessageBox.warning(None, f"HelPy — {title}", detail)
