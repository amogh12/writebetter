import sys
import time
import pyperclip
from pynput.keyboard import Controller, Key

_kb = Controller()
_COPY_KEY = Key.cmd if sys.platform == "darwin" else Key.ctrl

# All modifiers that might be held from the hotkey combo
_ALL_MODS = (
    Key.shift, Key.shift_l, Key.shift_r,
    Key.alt,   Key.alt_l,   Key.alt_r,
    Key.ctrl,  Key.ctrl_l,  Key.ctrl_r,
    Key.cmd,   Key.cmd_l,   Key.cmd_r,
)


def get_selected_text(sleep_ms: int = 150) -> str:
    """Simulate copy-key+C to copy selection, read clipboard, restore original."""
    # Release held modifiers from the hotkey combo so the app sees plain
    # Ctrl+C / Cmd+C, not Ctrl+Shift+C (which opens DevTools in Chrome/Edge).
    for key in _ALL_MODS:
        try:
            _kb.release(key)
        except Exception:
            pass

    saved = pyperclip.paste()
    pyperclip.copy("")
    _kb.press(_COPY_KEY)
    _kb.press("c")
    _kb.release("c")
    _kb.release(_COPY_KEY)
    time.sleep(sleep_ms / 1000)
    selected = pyperclip.paste()
    pyperclip.copy(saved)
    return selected
