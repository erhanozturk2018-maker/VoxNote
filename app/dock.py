"""Floating bar at the edge of the screen.

A small, frameless, always-on-top window that normally shows only a thin
strip at the left or right screen edge. When the pointer moves onto the
strip, the bar slides out and offers the most important controls: start or
stop the recording, the elapsed time, and a button that brings the main
window to the front. When the pointer leaves, it slides back.

How it works:

* window flags ``Tool | FramelessWindowHint | WindowStaysOnTopHint`` give a
  borderless window above other applications without a taskbar entry;
* ``enterEvent`` and ``leaveEvent`` detect hovering;
* a ``QPropertyAnimation`` on the window position produces the sliding;
* a short timer delays hiding so the bar does not flicker when the pointer
  briefly crosses its border.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.i18n import tr
from app.icons import icon, icon_size
from app.recording_controller import AppState, RecordingController
from app.theme import tokens
from app.transcript_models import format_clock

WIDTH = 64
HEIGHT = 176
# Part of the bar that stays visible while it is hidden.
STRIP = 8
SLIDE_MS = 160
HIDE_DELAY_MS = 450
RADIUS = 14
# The application style sheet gives buttons padding and a minimum height;
# the round buttons of the bar need an exact size instead.
_ROUND = "min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px;"


class EdgeDock(QWidget):
    start_requested = Signal()
    stop_requested = Signal()
    show_window_requested = Signal()

    def __init__(self, controller: RecordingController, edge: str = "right") -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(WIDTH, HEIGHT)
        self._controller = controller
        self._edge = edge if edge in ("left", "right") else "right"
        self._expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(10)
        self.record_button = self._button()
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window_button = self._button()
        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # The state is conveyed by the button, the grip colour and the tooltip;
        # state names are too long for a bar this narrow.
        self.state_label.hide()
        layout.addWidget(self.record_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.state_label)
        layout.addStretch(1)
        layout.addWidget(self.window_button, 0, Qt.AlignmentFlag.AlignHCenter)

        self.record_button.clicked.connect(self._toggle_recording)
        self.window_button.clicked.connect(self.show_window_requested)

        self._animation = QPropertyAnimation(self, b"pos", self)
        self._animation.setDuration(SLIDE_MS)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(HIDE_DELAY_MS)
        self._hide_timer.timeout.connect(self._collapse_if_left)
        self._clock = QTimer(self)
        self._clock.setInterval(500)
        self._clock.timeout.connect(self._update_clock)

        controller.state_changed.connect(self._on_state_changed)
        self.refresh()
        self.move(self._position(expanded=False))

    def _button(self) -> QPushButton:
        button = QPushButton()
        button.setFixedSize(40, 40)
        button.setIconSize(icon_size(20))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    # -- geometry --------------------------------------------------------

    def set_edge(self, edge: str) -> None:
        self._edge = edge if edge in ("left", "right") else "right"
        self._expanded = False
        self.move(self._position(expanded=False))
        self.update()

    def _position(self, expanded: bool) -> QPoint:
        screen = QGuiApplication.primaryScreen().availableGeometry()
        y = screen.top() + (screen.height() - HEIGHT) // 2
        if self._edge == "left":
            x = screen.left() if expanded else screen.left() - (WIDTH - STRIP)
        else:
            x = screen.right() + 1 - (WIDTH if expanded else STRIP)
        return QPoint(x, y)

    def _slide(self, expanded: bool) -> None:
        if expanded == self._expanded and self._animation.state() != QPropertyAnimation.State.Running:
            return
        self._expanded = expanded
        self._animation.stop()
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(self._position(expanded))
        self._animation.start()

    # -- hover -----------------------------------------------------------

    def enterEvent(self, event) -> None:
        self._hide_timer.stop()
        self._slide(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hide_timer.start()
        super().leaveEvent(event)

    def _collapse_if_left(self) -> None:
        if not self.geometry().contains(QCursor.pos()):
            self._slide(False)

    # -- content ---------------------------------------------------------

    def _toggle_recording(self) -> None:
        if self._controller.can_stop:
            self.stop_requested.emit()
        elif self._controller.can_start:
            self.start_requested.emit()

    def _on_state_changed(self, state: AppState) -> None:
        if state is AppState.RECORDING:
            self._clock.start()
        else:
            self._clock.stop()
        self.refresh()

    def _update_clock(self) -> None:
        elapsed = time.monotonic() - self._controller.started_monotonic
        self.timer_label.setText(format_clock(elapsed)[3:] if elapsed < 3600 else format_clock(elapsed))

    def refresh(self) -> None:
        """Update icons, colours and texts for the current state and theme."""
        colors = tokens()
        c = self._controller
        recording = c.state is AppState.RECORDING
        self.record_button.setEnabled(c.can_start or c.can_stop)
        if recording:
            self.record_button.setIcon(icon("stop", colors["record_text"], 20))
            background, hover = colors["record"], colors["record_hover"]
            self.record_button.setToolTip(tr("dock.stop", shortcut="Ctrl+Alt+R"))
        else:
            self.record_button.setIcon(icon("microphone", colors["accent_text"], 20))
            background, hover = colors["accent"], colors["accent_hover"]
            self.record_button.setToolTip(tr("dock.start", shortcut="Ctrl+Alt+R"))
        self.record_button.setAccessibleName(self.record_button.toolTip())
        self.record_button.setStyleSheet(
            f"QPushButton {{ background: {background}; border: none; border-radius: 20px; padding: 0; {_ROUND} }}"
            f"QPushButton:hover {{ background: {hover}; }}"
            f"QPushButton:disabled {{ background: {colors['disabled_bg']}; }}"
        )
        self.window_button.setIcon(icon("window", colors["text"], 20))
        self.window_button.setToolTip(tr("dock.show_window"))
        self.window_button.setAccessibleName(tr("dock.show_window"))
        self.window_button.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-radius: 20px; padding: 0; {_ROUND} }}"
            f"QPushButton:hover {{ background: {colors['info_bg']}; }}"
        )
        self.timer_label.setStyleSheet(
            f"color: {colors['text']}; font-size: 10pt; font-weight: 600; background: transparent;"
        )
        self.state_label.setStyleSheet(
            f"color: {colors['record'] if recording else colors['muted']}; font-size: 8pt; "
            "background: transparent;"
        )
        self.state_label.setText(tr(f"state.{c.state.value}"))
        self.timer_label.setToolTip(self.state_label.text())
        if not recording and not c.session.duration_seconds:
            self.timer_label.setText("00:00")
        self.update()

    def paintEvent(self, event) -> None:
        colors = tokens()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(colors["border"]))
        painter.setBrush(QColor(colors["card"]))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), RADIUS, RADIUS)
        # The visible strip: a coloured grip that turns red while recording.
        recording = self._controller.state is AppState.RECORDING
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors["record"] if recording else colors["accent"]))
        x = 2 if self._edge == "right" else self.width() - 6
        painter.drawRoundedRect(x, (self.height() - 56) // 2, 4, 56, 2, 2)
        painter.end()
