from PyQt5.QtCore import QVariantAnimation, QEasingCurve
from app.ui.shared.icons import get_icon


class AnimatedCollapseMixin:
    """Smooth collapse/expand animation for container widgets."""

    def _setup_collapse_animation(self, container, edge_button, duration=300):
        self._anim_container = container
        self._anim_edge_button = edge_button
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(duration)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_collapse_anim_step)
        self._anim.finished.connect(self._on_collapse_anim_finished)
        self._animating_collapse = False
        self._anim_header_height = 0

        if self.is_collapsed:
            container.setMaximumHeight(0)
            container.setVisible(False)

    def _on_collapse_anim_step(self, value):
        self._anim_container.setMaximumHeight(int(value))
        if self._animating_collapse and int(value) <= 2:
            self._anim_container.setVisible(False)
        elif not self._anim_container.isVisible():
            self._anim_container.setVisible(True)
        self.resize(self.width(), int(self._anim_header_height + value))

    def _on_collapse_anim_finished(self):
        if self.is_collapsed:
            self._anim_container.setVisible(False)
            self._anim_container.setMaximumHeight(0)
            self.resize(self.width(), int(self._anim_header_height))
        else:
            self._anim_container.setMaximumHeight(16777215)
            self.resize(self.width(), int(self._anim_header_height + self._anim_container.sizeHint().height()))
        self._animating_collapse = False

    def _header_height(self):
        if self._anim_container.isVisible():
            return max(1, self.height() - self._anim_container.height())
        return max(1, self.height())

    def _animate_toggle_collapsed(self):
        self._anim.stop()
        self._anim_header_height = self._header_height()
        self.is_collapsed = not self.is_collapsed
        self._animating_collapse = self.is_collapsed

        if not self.is_collapsed:
            self._anim_container.setVisible(True)
            self._anim_container.setMaximumHeight(16777215)
            target = self._anim_container.sizeHint().height()
            self._anim_container.setMaximumHeight(0)
            self.resize(self.width(), int(self._anim_header_height))
            self._anim.setStartValue(0)
            self._anim.setEndValue(target)
        else:
            self._anim_container.setMaximumHeight(16777215)
            start = self._anim_container.height() or self._anim_container.sizeHint().height()
            self.resize(self.width(), int(self._anim_header_height + start))
            self._anim.setStartValue(start)
            self._anim.setEndValue(0)

        self._anim_edge_button.setIcon(
            get_icon("expand" if self.is_collapsed else "collapse")
        )
        self._anim.start()
