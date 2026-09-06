from __future__ import annotations

import keyring
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QVBoxLayout,
)

# Maps Qt key codes to pynput key names
_DARK_CSS = """
QDialog, QWidget { font-family: 'Segoe UI', system-ui, sans-serif; font-size: 10pt; }
QLabel { background: transparent; }
QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #3d3d55;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #6366f1; }
QLineEdit:disabled { color: #55556a; }
QDialogButtonBox QPushButton {
    background: #6366f1; color: #fff;
    border: none; border-radius: 7px;
    padding: 7px 20px; font-weight: 600; min-width: 80px;
}
QDialogButtonBox QPushButton:hover { background: #4f52d8; }
QDialogButtonBox QPushButton[text="Cancel"] {
    background: transparent; color: #94a3b8; border: 1px solid #3d3d55;
}
QDialogButtonBox QPushButton[text="Cancel"]:hover { border-color: #6366f1; color: #e2e8f0; }
"""



_FN_KEYS = {
    Qt.Key.Key_F1: "<f1>",   Qt.Key.Key_F2: "<f2>",
    Qt.Key.Key_F3: "<f3>",   Qt.Key.Key_F4: "<f4>",
    Qt.Key.Key_F5: "<f5>",   Qt.Key.Key_F6: "<f6>",
    Qt.Key.Key_F7: "<f7>",   Qt.Key.Key_F8: "<f8>",
    Qt.Key.Key_F9: "<f9>",   Qt.Key.Key_F10: "<f10>",
    Qt.Key.Key_F11: "<f11>", Qt.Key.Key_F12: "<f12>",
}
_MODIFIER_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Shift,
    Qt.Key.Key_Alt, Qt.Key.Key_Meta,
}


class HotkeyEdit(QLineEdit):
    """Click to capture a key combination; displays it in pynput format."""

    def __init__(self, value: str, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(value)
        self._capturing = False

    def mousePressEvent(self, event: QKeyEvent) -> None:
        if self.isEnabled():
            self._start_capture()
        super().mousePressEvent(event)

    def _start_capture(self) -> None:
        self._prev = self.text()
        self._capturing = True
        self.setText("Press shortcut…")
        self.setStyleSheet("color: #888; font-style: italic;")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._capturing:
            return

        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.setText(self._prev)
            self.setStyleSheet("")
            self._capturing = False
            return

        if key in _MODIFIER_KEYS:
            return  # wait for a non-modifier

        mods = event.modifiers()
        parts: list[str] = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("<ctrl>")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("<alt>")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("<shift>")

        key_str = _FN_KEYS.get(key)
        if key_str is None and Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            key_str = chr(key).lower()
        elif key_str is None and Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            key_str = chr(key)

        if key_str:
            parts.append(key_str)
            self.setText("+".join(parts))
            self.setStyleSheet("")
            self._capturing = False
        # if key_str is None (unrecognised key) just keep waiting


class SettingsDialog(QDialog):
    needs_restart: bool = False

    def __init__(self, cfg: dict, save_fn, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._save_fn = save_fn
        self.setWindowTitle("WriteBetter — Settings")
        self.setMinimumWidth(480)
        self.setStyleSheet(_DARK_CSS)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._trigger = QComboBox()
        self._trigger.addItem("Ctrl+C  (popup on every copy)", "ctrl_c")
        self._trigger.addItem("Hotkey  (manual shortcut)", "hotkey")
        current_trigger = self._cfg.get("trigger", "hotkey")
        self._trigger.setCurrentIndex(0 if current_trigger == "ctrl_c" else 1)
        self._trigger.currentIndexChanged.connect(self._on_trigger_changed)
        form.addRow("Trigger:", self._trigger)

        self._hotkey = HotkeyEdit(self._cfg.get("hotkey", "<ctrl>+<shift>+<f9>"))
        hint = QLabel("Click to record")
        hint.setStyleSheet("color: #888; font-size: 9pt;")
        hotkey_row = QHBoxLayout()
        hotkey_row.addWidget(self._hotkey, 1)
        hotkey_row.addWidget(hint)
        form.addRow("Hotkey:", hotkey_row)

        self._num_variants = QSpinBox()
        self._num_variants.setRange(1, 9)
        self._num_variants.setValue(self._cfg.get("num_variants", 3))
        form.addRow("Variants:", self._num_variants)

        self._default_instr = QLineEdit(self._cfg.get("default_instructions", ""))
        form.addRow("Default instructions:", self._default_instr)

        self._active_provider = QComboBox()
        for p in self._cfg.get("providers", []):
            self._active_provider.addItem(p["id"])
        idx = self._active_provider.findText(self._cfg.get("active_provider", ""))
        if idx >= 0:
            self._active_provider.setCurrentIndex(idx)
        form.addRow("Active provider:", self._active_provider)

        layout.addLayout(form)

        layout.addWidget(QLabel("API Keys (stored in Windows Credential Manager):"))
        self._key_edits: dict[str, QLineEdit] = {}
        for p in self._cfg.get("providers", []):
            key_ref = p.get("key_ref", "")
            if not key_ref:
                continue
            row = QHBoxLayout()
            row.addWidget(QLabel(f"  {p['id']}:"))
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            existing = keyring.get_password("writebetter", key_ref)
            if existing:
                edit.setText(existing)
            edit.setPlaceholderText("sk-… or leave blank to keep")
            self._key_edits[key_ref] = edit
            row.addWidget(edit, 1)
            layout.addLayout(row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_trigger_changed()

    def _on_trigger_changed(self) -> None:
        is_hotkey = self._trigger.currentData() == "hotkey"
        self._hotkey.setEnabled(is_hotkey)

    def _save(self) -> None:
        self._cfg["trigger"] = self._trigger.currentData()
        self._cfg["hotkey"] = self._hotkey.text()
        self._cfg["num_variants"] = self._num_variants.value()
        self._cfg["default_instructions"] = self._default_instr.text()
        self._cfg["active_provider"] = self._active_provider.currentText()

        for key_ref, edit in self._key_edits.items():
            val = edit.text().strip()
            if val:
                keyring.set_password("writebetter", key_ref, val)

        self._save_fn(self._cfg)
        self.needs_restart = True
        self.accept()
