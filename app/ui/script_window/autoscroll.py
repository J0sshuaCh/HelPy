from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject

class AutoScrollManager(QObject):
    MIN_SPEED = 1
    MAX_SPEED = 10
    DEFAULT_SPEED = 3
    TICK_MS = 50

    stopped = pyqtSignal()

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self._speed = self.DEFAULT_SPEED
        self._is_active = False
        self._accumulator = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_MS)
        self._timer.timeout.connect(self._scroll_step)

    @property
    def is_active(self):
        return self._is_active

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = max(self.MIN_SPEED, min(self.MAX_SPEED, value))

    def toggle(self):
        if self._is_active:
            self.stop()
        else:
            self.start()

    def start(self):
        self._accumulator = 0.0
        self._is_active = True
        self._timer.start()

    def stop(self):
        self._is_active = False
        self._timer.stop()
        self.stopped.emit()

    def reset(self):
        self.stop()
        self._speed = self.DEFAULT_SPEED

    def _step_per_tick(self):
        return 0.3 * (1.6 ** (self._speed - 1))

    def _scroll_step(self):
        viewer = self.window.viewer_stack.currentWidget()
        scrollbar = None
        if viewer == self.window.md_view:
            scrollbar = viewer.verticalScrollBar()
        elif viewer == self.window.pdf_scroll:
            scrollbar = viewer.verticalScrollBar()

        if scrollbar is None:
            self.stop()
            return

        self._accumulator += self._step_per_tick()
        pixels = int(self._accumulator)
        if pixels <= 0:
            return

        self._accumulator -= pixels

        current = scrollbar.value()
        scrollbar.setValue(current + pixels)

        if scrollbar.value() >= scrollbar.maximum():
            self.stop()
