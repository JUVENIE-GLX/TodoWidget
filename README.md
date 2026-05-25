# TodoWidget - 桌面待办小组件

## 简介

Windows 桌面悬浮待办事项小组件，支持置顶、透明、最小化到托盘。

## 技术栈

- Python 3.8
- PyWebview (HTML/CSS/JS UI)
- PyInstaller 打包为 exe

## 核心文件

| 文件 | 说明 |
|------|------|
| `todo_widget.py` | 主程序源码 |
| `todo_widget.html` | UI 模板（HTML/CSS/JS） |
| `TodoWidget.spec` | PyInstaller 打包配置 |
| `TodoWidget.exe` | 打包产物（主程序） |
| `_internal/` | 运行时依赖（python38.dll 等） |
| `DEVELOPMENT.md` | 开发文档 |
| `todo_data.json` | 待办数据（自动生成） |
| `todo_settings.json` | 用户设置（自动生成） |

## 构建流程

修改 `todo_widget.py` 或 `todo_widget.html` 后必须重新打包：

```bash
cd D:/Claude_code/tasks/TodoWidget
pyinstaller TodoWidget.spec --distpath . --workpath build --clean
```

打包完成后移动产物并清理：

```bash
mv TodoWidget/TodoWidget.exe .
mv TodoWidget/_internal .
rmdir TodoWidget
rm -rf build __pycache__
```

## 使用方式

直接双击 `TodoWidget.exe` 启动。

### 功能

- 添加/删除/编辑待办
- 勾选完成（自动排序到底部）
- 拖拽排序
- 三种尺寸切换（红绿灯黄按钮）
- 最小化到托盘（绿按钮）
- 清空功能（已完成/待办/全部）
- 跨日自动继承未完成待办
- 窗口位置记忆

## 注意事项

- 使用已有的 `TodoWidget.spec` 文件打包，不要重新生成
- 每次重要功能更新后，同步更新 `DEVELOPMENT.md`
- exe 和 `_internal` 目录必须在同一级目录

## 进度

- [x] 基础待办功能
- [x] 桌面悬浮置顶
- [x] 系统托盘最小化
- [x] PyWebview 重写 UI
- [x] 修复删除待办重启残留 bug
- [ ] （按需添加）
