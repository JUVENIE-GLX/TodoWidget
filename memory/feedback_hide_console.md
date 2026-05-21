---
name: hide-console-window
description: "pywebview 打包后启动时隐藏终端窗口的方法"
metadata:
  type: feedback
---

pywebview 打包为 exe 后启动时会短暂弹出终端窗口，这是因为 pywebview 启动 Edge WebView2 时会创建子进程。

**Why:** 用户不希望看到任何终端窗口闪烁，影响体验。

**How to apply:**

在脚本最开头（import pywebview 之前）添加以下代码，monkey-patch subprocess：

```python
import sys
import os
import subprocess

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
```

打包命令必须使用 `--noconsole` 参数：
```bash
pyinstaller --noconsole --onefile --add-data "todo_widget.html;." --name TodoWidget todo_widget.py
```

注意：
- 必须在 import webview 之前执行 monkey-patch
- `CREATE_NO_WINDOW` 和 `STARTF_USESHOWWINDOW` 两个标志都需要设置
- 仅 Windows 平台需要
