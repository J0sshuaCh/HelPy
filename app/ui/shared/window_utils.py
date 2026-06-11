from PyQt5.QtWidgets import QApplication

def update_window_position(window, position_mode: str = "right"):
    """
    Updates the position of the window based on the position_mode.
    Valid modes are "left", "center", "right".
    """
    screen = QApplication.primaryScreen().availableGeometry()
    w = window.width()
    margin = 20

    if position_mode == "left":
        x = margin
    elif position_mode == "right":
        x = screen.width() - w - margin
    else:  # center
        x = int((screen.width() - w) / 2)

    window.move(x, margin)

def move_to_top_center(window):
    """Moves the window to the top center of the primary screen."""
    screen = QApplication.primaryScreen().availableGeometry()
    w = window.width()
    margin = 20
    x = int((screen.width() - w) / 2)
    window.move(x, margin)

def apply_window_size(window, max_width_ratio=0.40, max_pixels=480):
    """Applies a constrained width to the window based on screen size."""
    screen = QApplication.primaryScreen().availableGeometry()
    max_width = int(screen.width() * max_width_ratio)
    width = min(max_pixels, max_width)
    window.setFixedWidth(width)
    window.adjustSize()
