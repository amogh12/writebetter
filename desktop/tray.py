import sys

from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def _make_icon() -> QIcon:
    if sys.platform == "darwin":
        from pathlib import Path
        assets = Path(__file__).parent.parent / "assets"
        icon = QIcon()
        for size in (18, 36, 72):
            f = assets / f"icon_{size}.png"
            if f.exists():
                icon.addFile(str(f), QSize(size, size))
        if not icon.isNull():
            return icon

    # Windows / fallback: painted indigo circle with "W"
    px = QPixmap(22, 22)
    px.fill(QColor("transparent"))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#6366f1"))
    p.setPen(QColor("transparent"))
    p.drawEllipse(1, 1, 20, 20)
    p.setPen(QColor("#ffffff"))
    p.drawText(px.rect(), 0x84, "W")
    p.end()
    return QIcon(px)


def create_tray(show_settings_fn, on_double_click_fn, hotkey_str: str, quit_fn) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(_make_icon())
    tray.setToolTip(f"WriteBetter — {hotkey_str}")

    menu = QMenu()
    menu.addAction("Open WriteBetter", on_double_click_fn)
    menu.addAction("Settings…", show_settings_fn)
    menu.addSeparator()
    menu.addAction("Quit", quit_fn)
    tray.setContextMenu(menu)

    def _on_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            on_double_click_fn()
        # macOS sends Trigger (single left-click) instead of DoubleClick
        elif sys.platform == "darwin" and reason == QSystemTrayIcon.ActivationReason.Trigger:
            on_double_click_fn()

    tray.activated.connect(_on_activated)
    tray.show()

    # Startup balloon — slight delay so tray is fully ready
    QTimer.singleShot(
        800,
        lambda: tray.showMessage(
            "WriteBetter is running",
            f"Select text and press {hotkey_str} to rewrite it.",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        ),
    )

    return tray
