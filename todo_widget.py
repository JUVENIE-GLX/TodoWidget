import sys
import os
import subprocess

# Set .NET runtime for pythonnet (use .NET Framework for WinForms)
os.environ['PYTHONNET_RUNTIME'] = 'netfx'

# Monkey-patch subprocess to hide console windows
_original_popen = subprocess.Popen
def _hidden_popen(*args, **kwargs):
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        kwargs['startupinfo'] = startupinfo
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    return _original_popen(*args, **kwargs)
subprocess.Popen = _hidden_popen

import webview
import json
from datetime import datetime

if getattr(sys, 'frozen', False):
    _DIR = os.path.dirname(os.path.abspath(sys.executable))
    _DATA_DIR = os.path.join(_DIR, '_internal')
    if not os.path.isdir(_DATA_DIR):
        _DATA_DIR = _DIR
else:
    _DIR = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR = _DIR

DATA_FILE = os.path.join(_DATA_DIR, "todo_data.json")
SETTINGS_FILE = os.path.join(_DATA_DIR, "todo_settings.json")
HTML_FILE = os.path.join(_DATA_DIR, "todo_widget.html")

# Windows DWM API for rounded corners
try:
    import ctypes
    from ctypes import wintypes

    dwmapi = ctypes.windll.dwmapi
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWCP_ROUND = 2

    class _RECT(ctypes.Structure):
        _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                    ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

    def set_window_rounded(hwnd):
        """Set window rounded corners (Windows 11)"""
        try:
            preference = ctypes.c_int(DWMWCP_ROUND)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(preference),
                ctypes.sizeof(preference)
            )
        except Exception:
            pass
except ImportError:
    _RECT = None
    def set_window_rounded(hwnd):
        pass

SIZES = [("small", 280, 420), ("medium", 340, 540), ("large", 420, 660)]
SIZE_NAMES = [s[0] for s in SIZES]


def _get_primary_work_area():
    """Get primary monitor work area (excluding taskbar) using Windows API"""
    try:
        rect = _RECT()
        # SPI_GETWORKAREA = 0x0030
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        return None


def _clamp_to_primary(x, y, w, h):
    """Ensure window is within primary monitor bounds. Returns (x, y)."""
    area = _get_primary_work_area()
    if area is None:
        return x, y
    left, top, right, bottom = area
    screen_w = right - left
    screen_h = bottom - top

    # Check if window fits within primary screen (with some margin)
    if x is not None and y is not None:
        # Check if at least half the window is visible on primary screen
        if (left - w // 2) <= x <= (right - w // 2) and (top - h // 2) <= y <= (bottom - h // 2):
            return x, y

    # Default: center on primary screen
    return left + (screen_w - w) // 2, top + (screen_h - h) // 2


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return {}


def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Api:
    def __init__(self, window_ref):
        self._window_ref = window_ref
        self._dragging = False

    def load(self):
        """Load todo data and perform cleanup"""
        data = _load(DATA_FILE)
        today = datetime.now().strftime("%Y-%m-%d")
        had_today = today in data

        if today not in data:
            data[today] = []

        if not data[today] and not had_today:
            history = sorted([d for d in data if d < today], reverse=True)
            if history:
                pending = [dict(t) for t in data[history[0]] if not t.get("done")]
                if pending:
                    data[today] = pending

        seen = set()
        data[today] = [t for t in data[today] if t["text"] not in seen and not seen.add(t["text"])]

        changed = False
        for d in list(data.keys()):
            if d == today:
                continue
            before = len(data[d])
            data[d] = [t for t in data[d] if not t.get("done")]
            if not data[d]:
                del data[d]
            elif len(data[d]) != before:
                changed = True

        if changed or not had_today:
            _save(DATA_FILE, data)

        return json.dumps(data, ensure_ascii=False)

    def save(self, data_str):
        """Save todo data"""
        data = json.loads(data_str)
        _save(DATA_FILE, data)
        return True

    def close(self):
        """Close the window"""
        w = self._window_ref()
        if w:
            w.destroy()

    def minimize(self):
        """Minimize to tray (hide window)"""
        w = self._window_ref()
        if w:
            w.minimize()

    def cycle_size(self):
        """Cycle through sizes"""
        w = self._window_ref()
        if w:
            settings = _load(SETTINGS_FILE)
            current = settings.get("size", "medium")
            idx = SIZE_NAMES.index(current) if current in SIZE_NAMES else 1
            name, sw, sh = SIZES[(idx + 1) % 3]
            settings["size"] = name
            _save(SETTINGS_FILE, settings)
            w.resize(sw, sh)

    def start_drag(self, x, y):
        """Start window drag"""
        w = self._window_ref()
        if w:
            self._dragging = True
            self._drag_start_x = int(x)
            self._drag_start_y = int(y)
            try:
                pos = w.evaluate_js('JSON.stringify({x: window.screenX, y: window.screenY})')
                if pos:
                    pos_data = json.loads(pos)
                    self._win_start_x = pos_data['x']
                    self._win_start_y = pos_data['y']
            except Exception:
                self._win_start_x = 0
                self._win_start_y = 0

    def do_drag(self, x, y):
        """Move window during drag"""
        w = self._window_ref()
        if w and self._dragging:
            dx = int(x) - self._drag_start_x
            dy = int(y) - self._drag_start_y
            new_x = self._win_start_x + dx
            new_y = self._win_start_y + dy
            try:
                w.move(new_x, new_y)
            except Exception:
                pass

    def stop_drag(self):
        """Stop window drag"""
        self._dragging = False


def main():
    settings = _load(SETTINGS_FILE)
    size_key = settings.get("size", "medium")
    if size_key not in SIZE_NAMES:
        size_key = "medium"
    _, w, h = SIZES[SIZE_NAMES.index(size_key)]

    x = settings.get("x", None)
    y = settings.get("y", None)

    # Ensure window appears on primary monitor
    x, y = _clamp_to_primary(x, y, w, h)

    # Create window reference holder
    window = None

    def get_window():
        return window

    api = Api(get_window)

    # Read HTML content
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    window = webview.create_window(
        "待办",
        html=html_content,
        js_api=api,
        width=w,
        height=h,
        x=x,
        y=y,
        resizable=True,
        frameless=True,
        on_top=True,
        transparent=True,
    )

    # Save position on close
    def on_closed():
        try:
            pos = window.evaluate_js('JSON.stringify({x: window.screenX, y: window.screenY})')
            if pos:
                pos_data = json.loads(pos)
                settings = _load(SETTINGS_FILE)
                settings["x"] = pos_data.get("x")
                settings["y"] = pos_data.get("y")
                _save(SETTINGS_FILE, settings)
        except Exception:
            pass

    window.events.closed += on_closed

    def on_shown():
        """Set rounded corners when window is shown"""
        try:
            # Try to get native handle
            if hasattr(window, 'native_handle'):
                hwnd = window.native_handle
                if hwnd:
                    set_window_rounded(hwnd)
                    return

            # Fallback: use JS to get handle
            result = window.evaluate_js('window.pywebview._backend')
            if result:
                pass  # Handle via backend if needed
        except Exception:
            pass

        # Final fallback: enumerate windows
        try:
            import ctypes
            user32 = ctypes.windll.user32

            EnumWindows = user32.EnumWindows
            GetWindowTextW = user32.GetWindowTextW
            IsWindowVisible = user32.IsWindowVisible

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

            def enum_callback(hwnd, lparam):
                if IsWindowVisible(hwnd):
                    buf = ctypes.create_unicode_buffer(256)
                    GetWindowTextW(hwnd, buf, 256)
                    if "待办" in buf.value:
                        set_window_rounded(hwnd)
                        return False
                return True

            EnumWindows(WNDENUMPROC(enum_callback), 0)
        except Exception:
            pass

    window.events.shown += on_shown

    webview.start(debug=False)


if __name__ == "__main__":
    main()
