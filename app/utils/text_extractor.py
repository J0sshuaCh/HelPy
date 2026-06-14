import os

def extraer_texto(ruta: str) -> str:
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No existe: {ruta}")

    ext = ruta.lower()
    if ext.endswith((".md", ".markdown")):
        return _leer_texto(ruta)
    elif ext.endswith(".txt"):
        return _leer_texto(ruta)
    elif ext.endswith(".pdf"):
        return _extraer_pdf(ruta)
    else:
        raise ValueError(f"Formato no soportado: {ruta}")

def _leer_texto(ruta: str) -> str:
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(ruta, "r", encoding="latin-1", errors="replace") as f:
            return f.read()

def _extraer_pdf(ruta: str) -> str:
    import fitz
    doc = fitz.open(ruta)
    texto = "\n".join(page.get_text() for page in doc)
    doc.close()
    return texto
