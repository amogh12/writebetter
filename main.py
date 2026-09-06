import signal
import sys

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication

from core.config import load_config, save_config
from desktop.tray import create_tray


def _apply_dark_palette(app: QApplication) -> None:
    from PySide6.QtGui import QPalette, QColor
    app.setStyle("Fusion")
    p = QPalette()
    c = QColor
    p.setColor(QPalette.ColorRole.Window,          c("#1e1e2e"))
    p.setColor(QPalette.ColorRole.WindowText,       c("#e2e8f0"))
    p.setColor(QPalette.ColorRole.Base,             c("#2a2a3d"))
    p.setColor(QPalette.ColorRole.AlternateBase,    c("#252535"))
    p.setColor(QPalette.ColorRole.ToolTipBase,      c("#252535"))
    p.setColor(QPalette.ColorRole.ToolTipText,      c("#e2e8f0"))
    p.setColor(QPalette.ColorRole.Text,             c("#e2e8f0"))
    p.setColor(QPalette.ColorRole.Button,           c("#2a2a3d"))
    p.setColor(QPalette.ColorRole.ButtonText,       c("#e2e8f0"))
    p.setColor(QPalette.ColorRole.Link,             c("#818cf8"))
    p.setColor(QPalette.ColorRole.Highlight,        c("#6366f1"))
    p.setColor(QPalette.ColorRole.HighlightedText,  c("#ffffff"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       c("#55556a"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, c("#55556a"))
    app.setPalette(p)


class _Bridge(QObject):
    triggered = Signal(str)


_bridge: _Bridge | None = None
_cfg: dict = {}
_popup = None
_last_text: str = ""
_cache: dict[str, list] = {}   # provider_id -> variants, reset on each new trigger


def _on_trigger() -> None:
    """Called from pynput daemon thread."""
    global _cache
    try:
        from desktop.capture import get_selected_text
        text = get_selected_text(_cfg.get("key_sleep_ms", 150))
        print(f"[trigger] clipboard: {text!r:.80}", flush=True)
        if not text.strip():
            print("[trigger] clipboard empty, skipping", flush=True)
            return
        _cache = {}   # new text — discard old provider responses
        assert _bridge is not None
        _bridge.triggered.emit(text)
    except Exception as exc:
        print(f"[trigger ERROR] {exc}", file=sys.stderr, flush=True)


def _show_popup(text: str, initial_variants: list | None = None, initial_labels: list | None = None) -> None:
    global _popup, _last_text
    print("[popup] creating", flush=True)
    from desktop.popup import Popup

    if text:
        _last_text = text

    if _popup is not None:
        _popup.close()

    _popup = Popup(_cfg, text, initial_variants=initial_variants, initial_labels=initial_labels)
    _popup.apply_text.connect(_on_apply)
    _popup.variants_ready.connect(_store_variants)
    _popup.show()

    try:
        if sys.platform == "win32":
            import ctypes
            hwnd = int(_popup.winId())
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        elif sys.platform == "darwin":
            from desktop.platform_mac import activate_app
            activate_app()
            _popup.activateWindow()
            _popup.raise_()
        else:
            _popup.activateWindow()
            _popup.raise_()
    except Exception:
        _popup.activateWindow()
        _popup.raise_()


def _store_variants(provider_id: str, variants: list) -> None:
    global _cache
    _cache[provider_id] = variants


def _on_tray_open() -> None:
    """Double-click or 'Open' menu → show all cached provider responses, no API call."""
    if _cache:
        variants: list[str] = []
        labels: list[str] = []
        for pid, pvars in _cache.items():
            variants.extend(pvars)
            labels.extend([pid] * len(pvars))
        _show_popup(_last_text, initial_variants=variants, initial_labels=labels)
    else:
        _show_popup(_last_text)


def _on_apply(text: str) -> None:
    from desktop.replace import paste_text
    paste_text(text, _cfg.get("key_sleep_ms", 150))


def _show_settings() -> None:
    import subprocess
    from desktop.settings import SettingsDialog

    def _save_and_reload(new_cfg: dict) -> None:
        global _cfg
        save_config(new_cfg)
        _cfg = new_cfg

    dlg = SettingsDialog(_cfg, _save_and_reload)
    dlg.exec()

    if dlg.needs_restart:
        from pathlib import Path
        print("[main] restarting to apply settings…", flush=True)
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve())],
            cwd=str(Path(__file__).parent),
        )
        QApplication.instance().quit()


def main() -> None:
    global _cfg, _bridge

    _cfg = load_config()

    app = QApplication(sys.argv)
    _apply_dark_palette(app)
    app.setQuitOnLastWindowClosed(False)

    if sys.platform == "darwin":
        from desktop.platform_mac import hide_dock_icon
        hide_dock_icon()

    _bridge = _Bridge()
    _bridge.triggered.connect(_show_popup, Qt.ConnectionType.QueuedConnection)

    trigger_mode = _cfg.get("trigger", "hotkey")
    hotkey_str = _cfg.get("hotkey", "<ctrl>+<shift>+<f9>")
    display_hotkey = hotkey_str.replace("<", "").replace(">", "").replace("+", "+").title()

    tray = create_tray(_show_settings, _on_tray_open, display_hotkey, app.quit)  # noqa: F841

    # Let Python wake up every 250 ms so SIGINT (Ctrl+C in terminal) is handled.
    _sigint_timer = QTimer()
    _sigint_timer.start(250)
    _sigint_timer.timeout.connect(lambda: None)
    signal.signal(signal.SIGINT, lambda *_: app.quit())

    if trigger_mode == "ctrl_c":
        from desktop.hotkey import ClipboardTrigger
        listener = ClipboardTrigger(_on_trigger, delay_ms=_cfg.get("key_sleep_ms", 200))
        print(f"[main] trigger mode: ctrl_c")
    else:
        from desktop.hotkey import HotkeyListener
        listener = HotkeyListener(hotkey_str, _on_trigger)
        print(f"[main] trigger mode: hotkey ({hotkey_str})")

    listener.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
