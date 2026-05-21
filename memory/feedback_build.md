---
name: feedback-build
description: "修改 todo_widget.py 后必须立即用 PyInstaller 重新打包 exe"
metadata:
  type: feedback
---

每次修改 `todo_widget.py` 后，必须立即重新打包 exe。

**Why:** 用户需要 exe 保持最新，否则运行的是旧版本。

**How to apply:**
1. 修改 `D:\Claude_code\tasks\TodoWidget\todo_widget.py`
2. 执行：`cd D:/Claude_code/tasks/TodoWidget && pyinstaller TodoWidget.spec --distpath . --workpath build --clean`
3. 清理：`rm -rf build __pycache__`
4. 使用已有的 `TodoWidget.spec`，不要重新生成
