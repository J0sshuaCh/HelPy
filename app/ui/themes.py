PALETAS = {
    "Slate Minimalist (Oscuro)": {
        "fondo": "#1E293B",
        "fondo_input": "#0F172A",
        "texto": "#F8FAFC",
        "texto_secundario": "#94A3B8",
        "acento": "#2563EB",
        "borde": "#334155",
        "resaltado": "#60A5FA"
    },
    "Cyber Obsidian (Oscuro)": {
        "fondo": "#121214",
        "fondo_input": "#1A1A1E",
        "texto": "#FFFFFF",
        "texto_secundario": "#6B7280",
        "acento": "#10B981",
        "borde": "#2A2A30",
        "resaltado": "#34D399"
    },
    "Nordic Frost (Oscuro)": {
        "fondo": "#2E3440",
        "fondo_input": "#242933",
        "texto": "#ECEFF4",
        "texto_secundario": "#D8DEE9",
        "acento": "#88C0D0",
        "borde": "#3B4252",
        "resaltado": "#B48EAD"
    },
    "Tokyo Night (Oscuro)": {
        "fondo": "#1a1b26",
        "fondo_input": "#16161e",
        "texto": "#c0caf5",
        "texto_secundario": "#565f89",
        "acento": "#7aa2f7",
        "borde": "#292e42",
        "resaltado": "#bb9af7"
    },
    "Dark Earth (Oscuro)": {
        "fondo": "#2B2826",           # Tono café ultra oscuro (fondo de la imagen)
        "fondo_input": "#564b43",     # uno-5: Para cajas de texto y comboboxes
        "texto": "#ffdac2",           # uno-1: Tono crema para máxima legibilidad
        "texto_secundario": "#bd987f",# uno-2: Marrón claro para etiquetas de estado
        "acento": "#fecb52",          # duo-1: Amarillo oro brillante para llamadas a la acción
        "borde": "#705e51",           # uno-4: Marrón medio para delimitar sin saturar
        "resaltado": "#b09045"        # duo-2: Mostaza para barras de desplazamiento o hovers
    },
    "Dark Forest (Oscuro)": {
        "fondo": "#292C29",           # Tono oscuro general (basado en el fondo de la imagen)
        "fondo_input": "#585f58",     # uno-5: Verde grisáceo oscuro para inputs y cajas de texto
        "texto": "#ddf8dd",           # uno-1: Menta muy claro para máxima legibilidad
        "texto_secundario": "#a9bca9",# uno-2: Salvia claro para etiquetas y estado
        "acento": "#e7f98b",          # duo-1: Lima vibrante para botones principales y llamadas a la acción
        "borde": "#738273",           # uno-4: Salvia oscuro para delimitar sin saturar
        "resaltado": "#99a659"        # duo-2: Verde oliva para hovers y barras de desplazamiento
    },
    "Catppuccin Latte (Claro)": {
        "fondo": "#eff1f5",
        "fondo_input": "#e6e9ef",
        "texto": "#4c4f69",
        "texto_secundario": "#6c6f85",
        "acento": "#1e66f5",
        "borde": "#ccd0da",
        "resaltado": "#04a5e5"
    },
    "Light Emerald (Claro)": {
        "fondo": "#F4F7F5",
        "fondo_input": "#FFFFFF",
        "texto": "#1A2E22",
        "texto_secundario": "#607367",
        "acento": "#10B981",          # Verde esmeralda vibrante
        "borde": "#D1DBEC",
        "resaltado": "#34D399"
    },
    "Light Orchid (Claro)": {
        "fondo": "#FAF5F7",
        "fondo_input": "#FFFFFF",
        "texto": "#2E1A25",
        "texto_secundario": "#73606C",
        "acento": "#EC4899",          # Rosado orquídea
        "borde": "#EBD1DF",
        "resaltado": "#F472B6"
    },
    "Light Amber (Claro)": {
        "fondo": "#FAF7F4",
        "fondo_input": "#FFFFFF",
        "texto": "#2E241A",
        "texto_secundario": "#736760",
        "acento": "#F97316",          # Naranja energético
        "borde": "#EBDCD1",
        "resaltado": "#FB923C"
    },
    "Light Canary (Claro)": {
        "fondo": "#FBFBEE",
        "fondo_input": "#FFFFFF",
        "texto": "#2E2E1A",
        "texto_secundario": "#737360",
        "acento": "#EAB308",          # Amarillo ocre (oscurecido para legibilidad sobre blanco)
        "borde": "#EBEBD1",
        "resaltado": "#FDE047"
    },
    "Light Crimson (Claro)": {
        "fondo": "#FAF4F4",
        "fondo_input": "#FFFFFF",
        "texto": "#2E1A1A",
        "texto_secundario": "#736060",
        "acento": "#EF4444",          # Rojo carmesí
        "borde": "#EBD1D1",
        "resaltado": "#F87171"
    },
    "Light Amethyst (Claro)": {
        "fondo": "#F6F4FA",
        "fondo_input": "#FFFFFF",
        "texto": "#201A2E",
        "texto_secundario": "#656073",
        "acento": "#8B5CF6",          # Morado amatista
        "borde": "#D9D1EB",
        "resaltado": "#A78BFA"
    },
}

def obtener_qss(tema_nombre):
    t = PALETAS.get(tema_nombre, PALETAS["Slate Minimalist (Oscuro)"])
    
    return f"""
        QWidget {{ font-family: "Inter", "Segoe UI", sans-serif; }}
        #overlayContainer {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {t['fondo']}, stop:1 {t['fondo_input']});
            border: 1px solid {t['borde']};
            border-radius: 8px;
        }}
        QLabel {{ color: {t['texto']}; font-size: 12px; }}
        #statusLabel {{ color: {t['texto_secundario']}; font-size: 11px; }}
        #sectionLabel {{ font-size: 13px; font-weight: bold; color: {t['texto']}; }}
        #appTitle {{
            font-weight: bold;
            color: {t['acento']};
            font-size: 14px;
            background-color: {t['fondo_input']};
            border: 1px solid {t['borde']};
            border-radius: 8px;
            padding: 2px 10px;
        }}
        QComboBox, #deviceCombo, QLineEdit, QTextEdit#textArea {{
            background-color: {t['fondo_input']};
            color: {t['texto']};
            border: 1px solid {t['borde']};
            border-radius: 8px;
            padding: 6px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {t['fondo_input']};
            color: {t['texto']};
            border: 1px solid {t['borde']};
            selection-background-color: {t['acento']};
            selection-color: #FFFFFF;
        }}
        QPushButton {{
            background-color: {t['fondo']};
            color: {t['texto']};
            border: 1px solid {t['borde']};
            border-radius: 8px;
            padding: 6px 10px;
        }}
        QPushButton:hover {{
            background-color: {t['acento']};
            color: #FFFFFF;
        }}
        #sectionToggle, #edgeButton, #modeButton {{
            background-color: {t['fondo']};
            color: {t['texto']};
            border: 1px solid {t['borde']};
            border-radius: 8px;
        }}
        #sectionToggle:hover, #edgeButton:hover, #modeButton:hover, #modeButton:checked {{
            background-color: {t['acento']};
            color: #FFFFFF;
        }}
        QScrollBar:vertical {{ border: none; background: {t['fondo_input']}; width: 8px; }}
        QScrollBar::handle:vertical {{ background: {t['borde']}; border-radius: 4px; }}
        QSlider::groove:horizontal {{ background: {t['borde']}; height: 4px; border-radius: 2px; }}
        QSlider::handle:horizontal {{ background: {t['resaltado']}; border-radius: 7px; width: 14px; height: 14px; }}
    """
