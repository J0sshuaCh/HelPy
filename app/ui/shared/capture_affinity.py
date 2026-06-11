import sys
import ctypes

def apply_capture_affinity(window_id: int, capture_visible: bool):
    """
    Applies or removes the WDA_EXCLUDEFROMCAPTURE property for the given window.
    Only takes effect on Windows.
    """
    if sys.platform != "win32":
        return
        
    user32 = ctypes.windll.user32
    WDA_NONE = 0x00000000
    WDA_EXCLUDEFROMCAPTURE = 0x00000011
    
    affinity = WDA_NONE if capture_visible else WDA_EXCLUDEFROMCAPTURE
    result = user32.SetWindowDisplayAffinity(window_id, affinity)
    if not result:
        print("No se pudo aplicar la propiedad de exclusión de captura.")
