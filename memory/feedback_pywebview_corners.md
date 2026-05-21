---
name: pywebview-window-corners
description: "pywebview 无边框窗口实现 Windows 11 圆角的方法"
metadata:
  type: feedback
---

pywebview 的 `transparent=True` 参数不能直接实现窗口圆角，需要配合 Windows DWM API。

**Why:** pywebview 的透明设置在 Windows 上不完全生效，HTML/CSS 的圆角只是视觉效果，实际窗口仍是方角。用户期望的是系统级窗口圆角。

**How to apply:**

1. 使用 `ctypes` 调用 `dwmapi.DwmSetWindowAttribute` 设置 `DWMWA_WINDOW_CORNER_PREFERENCE = 33` 和 `DWMWCP_ROUND = 2`

2. 不能在 `on_loaded` 事件中直接获取窗口句柄（pywebview 的 `native_handle` 或 `_hwnd` 属性不可靠）

3. 正确方法：启动一个后台线程，等待 1 秒后通过 `win32gui.EnumWindows` 或 `ctypes` 的 `EnumWindows` 查找标题为 "待办" 的窗口句柄

4. 找到句柄后调用 `DwmSetWindowAttribute` 设置圆角

```python
# 关键代码
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2

def set_window_rounded(hwnd):
    preference = ctypes.c_int(DWMWCP_ROUND)
    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_WINDOW_CORNER_PREFERENCE,
        ctypes.byref(preference),
        ctypes.sizeof(preference)
    )
```

5. 注意：这是 Windows 11 特有功能，Windows 10 不支持
