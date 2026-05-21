# TodoWidget - 桌面待办小组件

## 简介

Windows 桌面悬浮待办事项小组件，支持置顶、透明、最小化到托盘。

## 技术栈

- Python 3
- PyInstaller 打包为 exe
- tkinter GUI

## 核心文件

| 文件 | 说明 |
|------|------|
| `todo_widget.py` | 主程序源码 |
| `TodoWidget.spec` | PyInstaller 打包配置（不要重新生成） |
| `TodoWidget.exe` | 打包产物 |
| `DEVELOPMENT.md` | 开发文档，记录功能和变更 |
| `todo_data.json` | 待办数据 |
| `todo_settings.json` | 用户设置 |

## 构建流程

修改 `todo_widget.py` 后必须重新打包：

```bash
cd D:/Claude_code/tasks/TodoWidget
pyinstaller TodoWidget.spec --distpath . --workpath build --clean
```

打包完成后清理：
```bash
rm -rf build __pycache__
```

## 注意事项

- 使用已有的 `TodoWidget.spec` 文件打包，不要重新生成
- 每次重要功能更新后，同步更新 `DEVELOPMENT.md`
- exe 生成在当前目录下（`--distpath .`）

## 进度

- [x] 基础待办功能
- [x] 桌面悬浮置顶
- [x] 系统托盘最小化
- [ ] （按需添加）
