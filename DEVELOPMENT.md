# TodoWidget 开发文档

## 项目概述

基于 PyWebview 的桌面悬浮待办清单 Widget，使用 HTML/CSS/JS 构建 UI，支持大中小三档视图、待办增删勾选、拖拽排序、数据持久化、跨日自动继承未完成待办。

---

## 文件结构

```
TodoWidget/
├── todo_widget.py      # Python 主程序（窗口、API、数据）
├── todo_widget.html    # UI 模板（HTML/CSS/JS）
├── TodoWidget.spec     # PyInstaller 打包配置
├── TodoWidget.exe      # 打包产物（主程序）
├── _internal/          # 运行时依赖（python38.dll 等）
├── todo_data.json      # 待办数据（自动生成）
├── todo_settings.json  # 视图设置（自动生成）
├── DEVELOPMENT.md      # 本文档
└── README.md           # 项目说明
```

---

## 技术架构

### 前端（todo_widget.html）

- 纯 HTML/CSS/JS，无框架依赖
- Apple 风格 UI（圆角、毛玻璃、SF Pro 字体）
- 通过 `window.pywebview.api` 调用 Python 后端

### 后端（todo_widget.py）

- PyWebview 创建无边框透明窗口
- `Api` 类暴露给前端的方法：
  - `load()` — 加载数据并执行清理/继承逻辑
  - `save(data_str)` — 保存数据到 JSON
  - `close()` — 关闭窗口
  - `minimize()` — 最小化到托盘
  - `cycle_size()` — 切换窗口尺寸
  - `start_drag(x, y)` / `do_drag(x, y)` / `stop_drag()` — 窗口拖动

---

## 配色方案（Apple 风格）

| 变量 | 色值 | 用途 |
|------|------|------|
| `--bg` | `#F2F2F7` | 窗口背景灰白 |
| `--card` | `rgba(255,255,255,0.85)` | 卡片白色（毛玻璃） |
| `--black` | `#1C1C1E` | 主文字 |
| `--gray` | `#8E8E93` | 次要文字/时钟 |
| `--light` | `#AEAEB2` | 占位符/已完成文字 |
| `--blue` | `#007AFF` | 强调色（+按钮/清空） |
| `--green` | `#34C759` | 勾选完成 |
| `--red` | `#FF3B30` | 关闭按钮 |

---

## 视图尺寸

| 档位 | 宽×高 |
|------|-------|
| small | 280×420 |
| medium | 340×540 |
| large | 420×660 |

缩放通过 CSS 变量 `--scale` 实现，JS 根据窗口宽度动态计算。

---

## 数据结构

### todo_data.json

```json
{
  "2026-05-25": [
    {"text": "写代码", "done": false},
    {"text": "买菜", "done": true}
  ]
}
```

- key = 日期字符串 `YYYY-MM-DD`
- value = 待办列表（数组）

### todo_settings.json

```json
{
  "size": "medium",
  "x": 800,
  "y": 40
}
```

---

## 路径兼容性

```python
if getattr(sys, 'frozen', False):
    _DIR = os.path.dirname(os.path.abspath(sys.executable))
    _DATA_DIR = os.path.join(_DIR, '_internal')
else:
    _DIR = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR = _DIR
```

- 开发模式：源码目录
- 打包模式：exe 同级的 `_internal` 目录

---

## 启动时自动继承与清理

每次启动调用 `load()` 时执行：

1. **判断是否有今天的记录** — 使用 `today in data` 而非 `bool(data.get(today))`
2. **继承未完成待办** — 仅当今天从未有过记录时，从最近的历史日期继承未完成待办
3. **清理历史已完成待办** — 遍历历史日期，删除 `done: true` 的项
4. **删除空日期条目** — 清理后没有内容的历史日期从数据中移除

### 关键修复（2026-05-25）

原代码用 `bool(data.get(today))` 判断，删除后列表为空返回 `False`，导致每次都重新从历史继承。

修复：改用 `today in data`，只要 JSON 中存在今天的 key（即使列表为空），就不再继承。

---

## 窗口圆角

使用 Windows 11 DWM API 实现原生圆角：

```python
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ...)
```

---

## 打包命令

```bash
cd D:/Claude_code/tasks/TodoWidget
pyinstaller TodoWidget.spec --distpath . --workpath build --clean
```

打包后需要手动移动产物：

```bash
mv TodoWidget/TodoWidget.exe .
mv TodoWidget/_internal .
rmdir TodoWidget
rm -rf build __pycache__
```

### 重要：所有代码修改必须同步更新 .exe

每次对 `todo_widget.py` 或 `todo_widget.html` 进行修改后，**必须重新执行打包命令**。

---

## 已知限制

1. **Python 3.8** — 使用较旧版本以兼容 PyInstaller
2. **Windows Only** — 使用了 Windows DWM API 和系统托盘
3. **字体依赖** — 使用 `Microsoft YaHei UI`，需 Windows 中文环境

---

## 后续可加功能参考

- [x] 双击待办修改
- [x] 跨日继承未完成待办
- [x] PyWebview 重写 UI
- [x] 修复删除待办重启残留 bug
- [ ] 多日待办切换（日期选择器）
- [ ] 待办分类/标签
- [ ] 搜索/过滤
- [ ] 导出/导入
- [ ] 快捷键支持
- [ ] 开机自启
- [ ] 深色模式
