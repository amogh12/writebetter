"""macOS-specific helpers using the ObjC runtime via ctypes — no PyObjC needed."""
import ctypes
import ctypes.util
import sys

if sys.platform != "darwin":
    raise ImportError("macOS only")

_lib = ctypes.util.find_library("objc")
_objc = ctypes.cdll.LoadLibrary(_lib) if _lib else None


def _send(obj, sel, *args, restype=ctypes.c_void_p, argtypes=None):
    """Call objc_msgSend with a fresh argtypes/restype each time (variadic ABI)."""
    if _objc is None:
        return None
    fn = _objc.objc_msgSend
    fn.restype = restype
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p] + (argtypes or [])
    return fn(obj, sel, *args)


def _cls(name: bytes):
    if _objc is None:
        return None
    _objc.objc_getClass.restype = ctypes.c_void_p
    return _objc.objc_getClass(name)


def _sel(name: bytes):
    if _objc is None:
        return None
    _objc.sel_registerName.restype = ctypes.c_void_p
    return _objc.sel_registerName(name)


def _shared_app():
    return _send(_cls(b"NSApplication"), _sel(b"sharedApplication"))


def hide_dock_icon() -> None:
    """Remove the app from the Dock — expected behaviour for menu-bar-only apps."""
    try:
        # NSApplicationActivationPolicyAccessory = 1
        _send(
            _shared_app(), _sel(b"setActivationPolicy:"),
            ctypes.c_long(1),
            argtypes=[ctypes.c_long],
        )
    except Exception as exc:
        print(f"[mac] hide_dock_icon failed: {exc}", flush=True)


def activate_app() -> None:
    """Bring the app to front, stealing focus from the active app."""
    try:
        _send(
            _shared_app(), _sel(b"activateIgnoringOtherApps:"),
            ctypes.c_bool(True),
            argtypes=[ctypes.c_bool],
        )
    except Exception as exc:
        print(f"[mac] activate_app failed: {exc}", flush=True)
