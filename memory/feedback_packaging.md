---
name: packaging-pywebview
description: "PyInstaller 打包 pywebview 项目的完整依赖配置和常见问题"
metadata:
  type: feedback
---

打包 pywebview + pythonnet 项目时必须检查以下配置，缺一不可：

**1. cffi C 扩展模块**
- `_cffi_backend.cpXX-win_amd64.pyd` 必须手动添加到 `binaries`，hiddenimports 无效
- XX 必须匹配当前 Python 版本（如 cp312）
- 文件位置：`D:/Python IDLE/Lib/site-packages/`

**2. pythonnet 相关隐藏导入**
```python
hiddenimports = [
    'clr', 'cffi', '_cffi_backend',
    'clr_loader', 'clr_loader.ffi', 'clr_loader.hostfxr',
    'pythonnet', 'webview', 'webview.platforms.winforms',
]
```

**3. .NET Runtime 环境变量**
- WinForms 后端需要 .NET Framework，不是 .NET Core
- 在 `import webview` 之前设置：`os.environ['PYTHONNET_RUNTIME'] = 'netfx'`
- 系统必须安装 .NET Framework 4.x

**Why:** pywebview 依赖链很长：`pywebview → pythonnet → clr_loader → cffi → .NET Framework`，任何一环缺失都会报错，且错误信息层层嵌套难以定位。

**How to apply:** 每次打包前检查 spec 文件中的 binaries 和 hiddenimports，确保 todo_widget.py 中有 `PYTHONNET_RUNTIME=netfx` 设置。打包后必须运行 exe 验证，不能只看打包成功就认为没问题。
