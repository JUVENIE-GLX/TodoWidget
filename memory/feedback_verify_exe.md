---
name: verify-after-build
description: "打包后必须自行运行 exe 验证，不能只看打包成功"
metadata:
  type: feedback
---

打包完成后必须运行 exe 验证功能正常，不能只看 PyInstaller 输出 "Build complete" 就认为没问题。

**Why:** 用户明确要求"完成任务要自行调试"。之前打包多次失败都是因为只看了打包日志就报告完成，结果用户运行时才发现报错。

**How to apply:** 每次打包后：
1. 运行 `TodoWidget.exe` 检查是否能正常启动
2. 测试基本功能（添加待办、勾选、删除）
3. 确认无报错后再向用户报告完成
