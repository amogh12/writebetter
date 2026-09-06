import sys
import threading

from pynput import keyboard


# ─────────────────────────────────────────── Windows low-level hook ──────────

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as wintypes

    user32 = ctypes.WinDLL('user32', use_last_error=True)

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN    = 0x0100
    WM_SYSKEYDOWN = 0x0104
    WM_QUIT       = 0x0012

    _LETTER_VK = {chr(c).lower(): 0x41 + (c - ord('A')) for c in range(ord('A'), ord('Z') + 1)}
    _DIGIT_VK  = {str(d): 0x30 + d for d in range(10)}
    _FN_VK     = {f'f{n}': 0x6F + n for n in range(1, 13)}
    _KEY_VK: dict[str, int] = {**_LETTER_VK, **_DIGIT_VK, **_FN_VK, 'space': 0x20}

    _MODIFIER_VK: dict[str, tuple[int, int]] = {
        'ctrl':  (0xA2, 0xA3),
        'shift': (0xA0, 0xA1),
        'alt':   (0xA4, 0xA5),
    }

    class _KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ('vkCode',      wintypes.DWORD),
            ('scanCode',    wintypes.DWORD),
            ('flags',       wintypes.DWORD),
            ('time',        wintypes.DWORD),
            ('dwExtraInfo', wintypes.LPARAM),
        ]

    _HookProc = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.c_int,
        ctypes.c_size_t,
        ctypes.c_ssize_t,
    )

    user32.CallNextHookEx.restype  = ctypes.c_long
    user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t]
    user32.SetWindowsHookExW.restype  = ctypes.c_void_p
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
    user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
    user32.PostThreadMessageW.argtypes  = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

    def _parse_hotkey(hotkey_str: str) -> tuple[set[str], int | None]:
        modifiers: set[str] = set()
        trigger_vk: int | None = None
        for token in hotkey_str.lower().split('+'):
            key = token.strip('<> ')
            if key in _MODIFIER_VK:
                modifiers.add(key)
            elif key in _KEY_VK:
                trigger_vk = _KEY_VK[key]
        return modifiers, trigger_vk

    class HotkeyListener:
        """
        Windows: raw WH_KEYBOARD_LL hook — suppresses the matched combo so
        the browser/editor never sees it. All other keys pass through normally.
        """

        def __init__(self, hotkey_str: str, callback):
            self._hotkey_str = hotkey_str
            self._callback   = callback
            self._modifiers, self._trigger_vk = _parse_hotkey(hotkey_str)
            self._hook:      int | None               = None
            self._thread:    threading.Thread | None  = None
            self._hook_proc: _HookProc | None         = None

        def _mod_held(self, mod: str) -> bool:
            return any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in _MODIFIER_VK[mod])

        def _build_proc(self) -> _HookProc:
            required = self._modifiers
            trigger  = self._trigger_vk
            all_mods = set(_MODIFIER_VK)
            cb       = self._callback

            def proc(nCode: int, wParam: int, lParam: int) -> int:
                if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN) and trigger is not None:
                    vk = ctypes.cast(lParam, ctypes.POINTER(_KBDLLHOOKSTRUCT)).contents.vkCode
                    if vk == trigger:
                        match = all(self._mod_held(m) == (m in required) for m in all_mods)
                        if match:
                            threading.Thread(target=cb, daemon=True).start()
                            return 1  # suppress
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            return _HookProc(proc)

        def start(self) -> None:
            if self._trigger_vk is None:
                print(f"[listener ERROR] unrecognised key in '{self._hotkey_str}'", file=sys.stderr, flush=True)
                return

            self._hook_proc = self._build_proc()

            def _run() -> None:
                self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._hook_proc, None, 0)
                if not self._hook:
                    err = ctypes.get_last_error()
                    print(f"[listener ERROR] hook install failed (err={err})", file=sys.stderr, flush=True)
                    return
                print(f"[listener] registered OK (suppressing): {self._hotkey_str}", flush=True)
                msg = wintypes.MSG()
                while user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                user32.UnhookWindowsHookEx(self._hook)
                self._hook = None

            self._thread = threading.Thread(target=_run, daemon=True, name="hotkey-hook")
            self._thread.start()

        def stop(self) -> None:
            if self._thread and self._thread.is_alive() and self._thread.ident:
                user32.PostThreadMessageW(self._thread.ident, WM_QUIT, 0, 0)

else:
    # ───────────────────────────── macOS / Linux: pynput GlobalHotKeys ───────
    # Mac browsers use Cmd for shortcuts; Ctrl+Shift+Fx combos don't conflict,
    # so pynput's simpler hook is sufficient (no custom suppression needed).

    class HotkeyListener:
        """macOS / Linux: pynput GlobalHotKeys listener."""

        def __init__(self, hotkey_str: str, callback):
            self._hotkey_str = hotkey_str
            self._callback   = callback
            self._hotkeys: keyboard.GlobalHotKeys | None = None

        def start(self) -> None:
            try:
                self._hotkeys = keyboard.GlobalHotKeys({self._hotkey_str: self._callback})
                self._hotkeys.start()
                print(f"[listener] registered OK: {self._hotkey_str}", flush=True)
            except Exception as exc:
                print(f"[listener ERROR] {exc}", file=sys.stderr, flush=True)
                if sys.platform == "darwin":
                    print("[listener] on macOS grant Accessibility permission: "
                          "System Settings → Privacy & Security → Accessibility", flush=True)

        def stop(self) -> None:
            if self._hotkeys:
                self._hotkeys.stop()


# ─────────────────────────────────────────── Clipboard trigger (all platforms) ──

class ClipboardTrigger:
    """Passively watches for Ctrl+C (Win/Linux) or Cmd+C (Mac); fires callback after delay."""

    _C_VK = 67  # virtual-key code for 'C'

    def __init__(self, callback, delay_ms: int = 200):
        self._callback = callback
        self._delay = delay_ms / 1000
        self._ctrl_down = False
        self._timer: threading.Timer | None = None
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        self._listener.start()
        print("[listener] clipboard trigger active", flush=True)

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()

    def _is_ctrl(self, key) -> bool:
        ctrl_keys = (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)
        if sys.platform == "darwin":
            ctrl_keys = (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r)
        return key in ctrl_keys

    def _on_press(self, key) -> None:
        if self._is_ctrl(key):
            self._ctrl_down = True
            return
        if self._ctrl_down and getattr(key, "vk", None) == self._C_VK:
            print("[trigger] copy detected — scheduling clipboard read", flush=True)
            self._schedule()

    def _on_release(self, key) -> None:
        if self._is_ctrl(key):
            self._ctrl_down = False

    def _schedule(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(self._delay, self._fire)
        self._timer.daemon = True
        self._timer.start()

    def _fire(self) -> None:
        try:
            self._callback()
        except Exception as exc:
            print(f"[trigger ERROR] {exc}", file=sys.stderr, flush=True)
