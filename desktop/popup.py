from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QThread, QPoint, QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

_STYLE_LABELS = {
    1: ["Rewritten"],
    2: ["Concise", "Expanded"],
    3: ["Minimal", "Polished", "Concise"],
}
_BADGE_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
                 "#06b6d4", "#f97316", "#84cc16", "#ec4899"]

def _make_css(dark: bool) -> str:
    if dark:
        shell_bg, shell_border   = "#1e1e2e", "#3d3d55"
        bar_bg,   bar_border     = "#171728", "#2d2d45"
        name_color               = "#94a3b8"
        close_hover_bg           = "#3d1f1f"
        close_hover_fg           = "#f87171"
        instr_bg, instr_border   = "#2a2a3d", "#3d3d55"
        instr_fg                 = "#e2e8f0"
        instr_focus              = "#6366f1"
        instr_bg_focus           = "#252540"
        regen_dis                = "#3d3d6a"
        card_bg, card_border     = "#252538", "#3d3d55"
        card_hbg, card_hborder   = "#2e2e50", "#6366f1"
        copy_bg, copy_fg         = "#2e2e4e", "#818cf8"
        copy_hbg                 = "#383870"
        status_fg                = "#64748b"
        scroll_handle            = "#4a4a6a"
    else:
        shell_bg, shell_border   = "#ffffff", "#dde1ea"
        bar_bg,   bar_border     = "#f5f6fa", "#e4e6ef"
        name_color               = "#4a5568"
        close_hover_bg           = "#fde8e8"
        close_hover_fg           = "#e53e3e"
        instr_bg, instr_border   = "#fafafa", "#dde1ea"
        instr_fg                 = "#2d3748"
        instr_focus              = "#6366f1"
        instr_bg_focus           = "#ffffff"
        regen_dis                = "#c7c9f5"
        card_bg, card_border     = "#f8f9fb", "#e4e6ef"
        card_hbg, card_hborder   = "#eef0ff", "#6366f1"
        copy_bg, copy_fg         = "#f0f1fa", "#6366f1"
        copy_hbg                 = "#e0e1ff"
        status_fg                = "#9ca3af"
        scroll_handle            = "#d1d5db"

    return f"""
* {{ font-family: 'Segoe UI', system-ui, sans-serif; font-size: 10pt; }}

QWidget#outer {{ background: transparent; }}

QFrame#shell {{
    background: {shell_bg};
    border: 1px solid {shell_border};
    border-radius: 12px;
}}
QFrame#titleBar {{
    background: {bar_bg};
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid {bar_border};
}}
QLabel#appName {{
    color: {name_color};
    font-weight: 600;
    font-size: 9pt;
}}
QPushButton#closeBtn {{
    background: transparent;
    border: none;
    color: #888;
    font-size: 14px;
    min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px;
    border-radius: 13px;
    padding: 0;
    qproperty-text: "✕";
}}
QPushButton#closeBtn:hover {{ background: {close_hover_bg}; color: {close_hover_fg}; }}

QLineEdit#instrField {{
    border: 1px solid {instr_border};
    border-radius: 7px;
    padding: 7px 10px;
    background: {instr_bg};
    color: {instr_fg};
}}
QLineEdit#instrField:focus {{
    border-color: {instr_focus};
    background: {instr_bg_focus};
}}

QPushButton#regenBtn {{
    background: #6366f1;
    color: #fff;
    border: none;
    border-radius: 7px;
    padding: 7px 16px;
    font-weight: 600;
    min-width: 90px;
}}
QPushButton#regenBtn:hover {{ background: #4f52d8; }}
QPushButton#regenBtn:disabled {{ background: {regen_dis}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ width: 5px; background: transparent; }}
QScrollBar::handle:vertical {{
    background: {scroll_handle}; border-radius: 2px; min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLabel#statusLbl {{ color: {status_fg}; padding: 32px; font-size: 10pt; }}

QPushButton#copyBtn {{
    background: {copy_bg};
    border: none;
    border-radius: 5px;
    padding: 4px 10px;
    color: {copy_fg};
    font-size: 9pt;
    min-width: 44px;
}}
QPushButton#copyBtn:hover {{ background: {copy_hbg}; }}
"""


# card stylesheets set per-instance (need the theme colors)
def _card_css(dark: bool) -> tuple[str, str]:
    if dark:
        return (
            "QFrame { background:#252538; border:1px solid #3d3d55; border-radius:8px; }",
            "QFrame { background:#2e2e50; border:1px solid #6366f1; border-radius:8px; }",
        )
    return (
        "QFrame { background:#f8f9fb; border:1px solid #e4e6ef; border-radius:8px; }",
        "QFrame { background:#eef0ff; border:1px solid #6366f1; border-radius:8px; }",
    )


# ─────────────────────────────────────────────────────────────── title bar ──

class _TitleBar(QFrame):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 0, 8, 0)

        icon = QLabel("✏")
        icon.setStyleSheet("color: #6366f1; font-size: 11pt;")
        name = QLabel("WriteBetter")
        name.setObjectName("appName")

        close = QPushButton()
        close.setObjectName("closeBtn")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(parent.close)

        row.addWidget(icon)
        row.addSpacing(6)
        row.addWidget(name)
        row.addStretch()
        row.addWidget(close)

    def mousePressEvent(self, event: QKeyEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.window().windowHandle().startSystemMove()


class _ResizeGrip(QLabel):
    """Bottom-right corner grip using native OS resize."""

    def __init__(self, window: QWidget, parent: QWidget):
        super().__init__("⠿", parent)
        self._window = window
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color: #c8ccd8; font-size: 13px;")

    def mousePressEvent(self, event: QKeyEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._window.windowHandle().startSystemResize(
                Qt.Edge.RightEdge | Qt.Edge.BottomEdge
            )


# ─────────────────────────────────────────────────────────────── card ──

class _Card(QFrame):
    clicked = Signal(str)

    def __init__(self, text: str, index: int, n: int, dark: bool, provider_label: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.text = text
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._normal_ss, self._hover_ss = _card_css(dark)
        self.setStyleSheet(self._normal_ss)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(6)

        # Header row: badge + style label + copy button
        header = QHBoxLayout()
        header.setSpacing(8)

        color = _BADGE_COLORS[(index - 1) % len(_BADGE_COLORS)]
        badge = QLabel(str(index))
        badge.setFixedSize(22, 22)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:{color}; color:#fff; border-radius:11px;"
            f" font-size:9pt; font-weight:700;"
        )
        badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header.addWidget(badge)

        labels = _STYLE_LABELS.get(n, [])
        if index - 1 < len(labels):
            style_lbl = QLabel(labels[index - 1])
            style_lbl.setStyleSheet(f"color:{color}; font-size:9pt; font-weight:600;")
            style_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            header.addWidget(style_lbl)

        if provider_label:
            prov_tag = QLabel(provider_label)
            prov_tag.setStyleSheet("color: #888; font-size: 8pt; font-style: italic;")
            prov_tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            header.addWidget(prov_tag)

        header.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("copyBtn")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.text))
        header.addWidget(copy_btn)

        outer.addLayout(header)

        # Body text
        body = QLabel(text)
        body.setWordWrap(True)
        body.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        outer.addWidget(body)

    def mousePressEvent(self, event: QKeyEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.text)

    def enterEvent(self, _e) -> None:
        self.setStyleSheet(self._hover_ss)

    def leaveEvent(self, _e) -> None:
        self.setStyleSheet(self._normal_ss)


# ─────────────────────────────────────────────────────────────── worker ──

class _Worker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, provider, model: str, text: str, instructions: str, n: int):
        super().__init__()
        self._provider = provider
        self._model = model
        self._text = text
        self._instructions = instructions
        self._n = n

    def run(self) -> None:
        import httpx
        from core.variants import get_variants
        try:
            self.finished.emit(
                get_variants(self._provider, self._model, self._text, self._instructions, self._n)
            )
        except httpx.ReadTimeout:
            self.error.emit("Request timed out — provider is slow. Try again or switch provider.")
        except Exception as exc:
            self.error.emit(str(exc))


# ─────────────────────────────────────────────────────────────── popup ──

class Popup(QWidget):
    apply_text = Signal(str)
    variants_ready = Signal(str, list)   # (provider_id, variants) after every successful generation

    def __init__(
        self,
        cfg: dict,
        text: str,
        initial_variants: list | None = None,
        initial_labels: list[str] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._cfg = cfg
        self._text = text
        self._worker: _Worker | None = None
        self._cards: list[_Card] = []
        self._dark = True
        self._status_lbl: QLabel | None = None
        self._elapsed: int = 0
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)

        self.setObjectName("outer")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(_make_css(self._dark))
        self.setMinimumSize(520, 340)
        self._build_ui()
        self._position_near_cursor()
        if initial_variants:
            self._show_variants(initial_variants, initial_labels)   # cached — no API call
        else:
            self._regenerate()

    # ── build ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Outer layout has margins so shadow has room
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        shell = QFrame()
        shell.setObjectName("shell")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 55))
        shell.setGraphicsEffect(shadow)

        outer.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        layout.addWidget(_TitleBar(self))

        # Body padding
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 10)
        body_layout.setSpacing(10)

        # Instructions + regenerate
        instr_row = QHBoxLayout()
        self._instr = QLineEdit(self._cfg.get("default_instructions", ""))
        self._instr.setObjectName("instrField")
        self._instr.setPlaceholderText("Instructions… (Enter to regenerate)")
        self._instr.returnPressed.connect(self._regenerate)
        instr_row.addWidget(self._instr, 1)

        self._regen_btn = QPushButton("↺  Regenerate")
        self._regen_btn.setObjectName("regenBtn")
        self._regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._regen_btn.clicked.connect(self._regenerate)
        instr_row.addWidget(self._regen_btn)
        body_layout.addLayout(instr_row)

        # Cards scroll area
        self._cards_w = QWidget()
        self._cards_w.setStyleSheet("background: transparent;")
        self._cards_vbox = QVBoxLayout(self._cards_w)
        self._cards_vbox.setContentsMargins(0, 0, 0, 0)
        self._cards_vbox.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidget(self._cards_w)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        body_layout.addWidget(scroll, 1)

        # Footer: provider + resize grip
        footer = QHBoxLayout()
        self._combo = QComboBox()
        for p in self._cfg.get("providers", []):
            self._combo.addItem(p["id"], p)
        active = self._cfg.get("active_provider", "")
        idx = self._combo.findText(active)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        self._combo.currentIndexChanged.connect(self._regenerate)
        footer.addWidget(self._combo)
        footer.addStretch()
        footer.addWidget(_ResizeGrip(self, body))
        body_layout.addLayout(footer)

        layout.addWidget(body)

    # ── logic ──────────────────────────────────────────────────────────────

    def _clear_cards(self) -> None:
        self._status_lbl = None
        while self._cards_vbox.count():
            item = self._cards_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards = []

    def _set_status(self, msg: str) -> None:
        self._clear_cards()
        lbl = QLabel(msg)
        lbl.setObjectName("statusLbl")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        self._cards_vbox.addWidget(lbl)
        self._status_lbl = lbl

    def _tick_elapsed(self) -> None:
        self._elapsed += 1
        if self._status_lbl is not None:
            self._status_lbl.setText(f"Generating variants… ({self._elapsed}s)")

    def _regenerate(self) -> None:
        if not self._text.strip():
            self._set_status(
                "Select text anywhere, then press your hotkey to get rewrite suggestions."
            )
            return

        if self._worker and self._worker.isRunning():
            self._elapsed_timer.stop()
            self._worker.finished.disconnect()
            self._worker.error.disconnect()
            self._worker.terminate()
            self._worker.wait(200)

        self._elapsed = 0
        self._regen_btn.setEnabled(False)
        self._set_status("Generating variants…")
        self._elapsed_timer.start()

        provider_data: dict | None = self._combo.currentData()
        if not provider_data:
            self._set_status("No provider selected.")
            return

        from core.config import make_provider
        try:
            provider = make_provider(provider_data)
        except Exception as exc:
            self._set_status(f"Config error: {exc}")
            self._regen_btn.setEnabled(True)
            return

        n = self._cfg.get("num_variants", 3)
        self._worker = _Worker(provider, provider_data["model"], self._text, self._instr.text(), n)
        self._worker.finished.connect(self._on_variants)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _show_variants(self, variants: list, labels: list[str] | None = None) -> None:
        self._clear_cards()
        n = len(variants)
        for i, v in enumerate(variants, 1):
            lbl = labels[i - 1] if labels and i - 1 < len(labels) else ""
            card = _Card(v, i, n, self._dark, provider_label=lbl)
            card.clicked.connect(self._on_apply)
            self._cards_vbox.addWidget(card)
            self._cards.append(card)
        self._cards_vbox.addStretch()
        self._regen_btn.setEnabled(True)

    def _on_variants(self, variants: list) -> None:
        self._elapsed_timer.stop()
        provider_id = ""
        data = self._combo.currentData()
        if data:
            provider_id = data.get("id", "")
        self._show_variants(variants, [provider_id] * len(variants))
        self.variants_ready.emit(provider_id, variants)

    def _on_error(self, msg: str) -> None:
        self._elapsed_timer.stop()
        self._set_status(f"⚠  {msg}")
        self._regen_btn.setEnabled(True)

    def _on_apply(self, text: str) -> None:
        self.apply_text.emit(text)
        self.close()

    def _position_near_cursor(self) -> None:
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos)
        if not screen:
            return
        geo = screen.availableGeometry()
        x = max(geo.left(), min(pos.x(), geo.right() - self.minimumWidth() - 24))
        y = max(geo.top(), min(pos.y() + 20, geo.bottom() - 500))
        self.move(x, y)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            idx = key - Qt.Key.Key_1
            if idx < len(self._cards):
                self._on_apply(self._cards[idx].text)
        else:
            super().keyPressEvent(event)
