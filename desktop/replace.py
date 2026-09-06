import sys
import time
import pyperclip
from pynput.keyboard import Controller, Key

_kb = Controller()
_PASTE_KEY = Key.cmd if sys.platform == "darwin" else Key.ctrl


def paste_text(text: str, sleep_ms: int = 150) -> None:
    saved = pyperclip.paste()
    pyperclip.copy(text)
    _kb.press(_PASTE_KEY)
    _kb.press("v")
    _kb.release("v")
    _kb.release(_PASTE_KEY)
    time.sleep(sleep_ms / 1000)
    pyperclip.copy(saved)
