# TodoWidget 开发文档

## 项目概述

基于 tkinter 的桌面悬浮待办清单 Widget，支持大中小三档视图、待办增删勾选、拖拽排序、滚轮滚动、数据持久化、跨日自动继承未完成待办。

---

## 文件结构

```
TodoWidget/
├── todo_widget.py      # 主程序（唯一源文件）
├── TodoWidget.spec     # PyInstaller 打包配置
├── todo_data.json      # 待办数据（自动生成）
├── todo_settings.json  # 视图设置（自动生成）
├── TodoWidget.exe      # 打包产物
└── DEVELOPMENT.md      # 本文档
```

---

## 配色方案（Apple 风格）

| 变量 | 色值 | 用途 |
|------|------|------|
| `BG` | `#F2F2F7` | 窗口背景灰白 |
| `CARD` | `#FFFFFF` | 卡片白色（输入栏/待办条） |
| `BORDER` | `#E5E5EA` | 分割线/边框 |
| `BLACK` | `#1D1D1F` | 主文字 |
| `GRAY` | `#8E8E93` | 次要文字/时钟 |
| `LIGHT` | `#AEAEB2` | 占位符/已完成文字 |
| `BLUE` | `#007AFF` | 强调色（+按钮/清空） |
| `GREEN` | `#34C759` | 勾选完成 |
| `RED` | `#FF3B30` | 关闭按钮 |
| `YELLOW` | `#FF9500` | 切换视图按钮 |

---

## 视图尺寸

三档等比缩放，基准宽度 `BW = 420`（large）。

| 档位 | 宽×高 | 缩放比 |
|------|-------|--------|
| small | 260×409 | 0.619 |
| medium | 340×534 | 0.810 |
| large | 420×660 | 1.000 |

缩放函数：`_si(w, v) = max(1, round(v * w / BW))`

---

## 布局结构

```
TodoWidget (Tk, overrideredirect)
└── bg (Canvas, 灰色圆角背景)
    └── main (Frame, BG)
        ├── hdr (Frame, BG) — header 行
        │   ├── [红] [黄] [绿] 三个圆点按钮
        │   ├── "待办" 标题
        │   ├── "5月17日 周六" 日期
        │   ├── "清空" + "▾" 清空按钮组
        │   └── "14:30" 时钟（右侧）
        └── body (Frame, BG)
            ├── bar (Frame, CARD) — 输入栏白卡
            │   ├── "+" 按钮
            │   └── Entry 输入框
            └── wrap (Frame, BG)
                └── _lc_cv (Canvas) — 可滚动列表
                    └── lc (Frame, BG) — 列表容器
                        ├── row (Frame, CARD) — 待办白卡
                        │   └── inner (Frame, CARD)
                        │       ├── cb (Canvas) — 勾选圆圈
                        │       ├── lbl (Label) — 待办文字（双击可编辑）
                        │       └── dl (Label) — 删除"×"（悬停显示）
                        └── ...更多 row
```

### 边距规则

- 窗口圆角半径 = `p["m"]`（即 margin）
- 所有内容区 `padx = p["m"]`，保证左右对称
- 待办条间距 `pady = p["m"] // 2`
- 输入栏与列表间距 = `p["m"] // 2`

---

## 窗口圆角实现

通过 Canvas 绘制四角圆弧实现窗口外层圆角（灰色）：

```python
def _draw_bg(self, w, h):
    r = p["m"]
    # 四个 arc（90°扇形）+ 两个矩形 = 圆角矩形
    cv.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=BG, ...)
    cv.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=BG, ...)
    cv.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=BG, ...)
    cv.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=BG, ...)
    cv.create_rectangle(r, 0, w-r, h, fill=BG, ...)
    cv.create_rectangle(0, r, w, h-r, fill=BG, ...)
```

### 关键注意事项

- **不要对单个卡片使用 canvas 圆角方案**。经过反复测试，tkinter 的 canvas + pack/place 方案存在以下致命问题：
  - `canvas` + `create_window` → frame 尺寸不自动扩展（pack propagation 失效）
  - `canvas` overlay（place）→ 阻断鼠标事件
  - `canvas` 同色弧线 → 无法看到圆角效果
  - `PIL ImageTk` + `Label` → 图片被子控件遮挡
- **结论**：tkinter 不支持透明 canvas，所有圆角卡片方案均不可靠。当前使用纯矩形白色卡片。

---

## 滚动实现

- Canvas 承载列表 Frame（`create_window`）
- 鼠标滚轮全局绑定（`bind_all("<MouseWheel>")`）
- 仅当鼠标在 canvas 区域内且内容超出可视高度时才滚动
- 无视觉滚动条（避免边距不对齐问题）

```python
def _on_wheel(self, e):
    # 检查鼠标是否在 canvas 区域内
    if x <= e.x_root <= x + w and y <= e.y_root <= y + h:
        # 检查内容是否超出可视区域
        sr = self._lc_cv.cget("scrollregion").split()
        if len(sr) == 4 and int(sr[3]) > h:
            self._lc_cv.yview_scroll(int(-1 * (e.delta / 120)), "units")
```

---

## 数据结构

### todo_data.json

```json
{
  "2026-05-17": [
    {"text": "写代码", "done": false},
    {"text": "买菜", "done": true}
  ]
}
```

- key = 日期字符串 `YYYY-MM-DD`
- value = 待办列表（数组）
- 超过 30 天的旧数据自动清理

### todo_settings.json

```json
{
  "size": "medium",
  "x": 800,
  "y": 40
}
```

### 持久化时机

| 操作 | 是否保存 |
|------|---------|
| 添加待办 | ✅ `_save_data()` |
| 勾选/取消 | ✅ `_save_data()` |
| 删除 | ✅ `_save_data()` |
| 编辑待办 | ✅ `_edit_save()` → `_save_data()` |
| 拖拽排序 | ✅ `_save_data()` |
| 清空 | ✅ `_save_data()` |
| 关闭窗口 | ✅ `_close()` 保存数据+设置 |
| 切换视图 | ✅ `_cycle()` 保存设置 |
| 启动时继承/清理 | ✅ `_save_data()`（有变更时） |

### 路径兼容性

```python
_DIR = os.path.dirname(os.path.abspath(
    sys.executable if getattr(sys, 'frozen', False) else __file__
))
```

- 开发模式：`__file__` 定位
- 打包模式（PyInstaller）：`sys.executable` 定位到 exe 目录

---

## 窗口拖动

整个窗口任意灰色区域可拖动。绑定位置：

| 绑定对象 | 说明 |
|---------|------|
| `self.bg` | 主 canvas（窗口背景） |
| `hdr` | header 帧 |
| `self.body` | body 帧 |
| `self._lc_cv` | 列表 canvas |

拖动使用全局坐标（`e.x_root` / `e.y_root`），避免子控件偏移问题。

```python
def _start_drag(self, e):
    self._drag = (e.x_root - self.winfo_x(), e.y_root - self.winfo_y())
def _do_drag(self, e):
    if self._drag:
        self.geometry(f"+{e.x_root-self._drag[0]}+{e.y_root-self._drag[1]}")
```

---

## 拖拽排序

- 按下记录位置，移动 ≥8px 启动拖拽（区分点击和拖拽）
- 拖拽中 widget 用 `place()` 跟随鼠标，`lift()` 保持最顶层
- 背景色变为 `#E8F0FE`（浅蓝）标识被拖拽项
- 松手后交换数据位置，保存并重新渲染
- 显示顺序为倒序（最新在上），数据索引需要 `real_idx = len(items) - 1 - i` 转换

---

## 双击编辑待办

双击待办文字（`lbl`），将 Label 替换为 Entry 输入框进行 inline 编辑。

### 实现要点

- 绑定 `<Double-Button-1>` 到 `lbl`，触发 `_edit_start(idx)`
- `_edit_start`：`pack_forget` 隐藏 Label，在同位置 `pack` 一个 Entry，预填原文并全选
- `_edit_save`：Enter 或 FocusOut 时保存，空内容则丢弃（恢复原文）
- `_edit_cancel`：Escape 时取消，恢复原文

### 关键注意事项：`_item_release` 不可无条件调用 `_render()`

**踩坑记录**：`_item_release`（`<ButtonRelease-1>`）如果每次都调用 `_render()`，会导致第一次点击松开时所有 widget 被销毁重建。第二次点击发生在新 widget 上，`<Double-Button-1>` 无法在同一个 widget 上累积触发，双击编辑永远不生效。

```python
def _item_release(self, e):
    r = self._reorder
    if not r:
        return
    if r["started"]:
        # 真正拖拽过 → 保存数据 + 重建
        ...
        self._reorder = None
        self._render()
    else:
        # 仅点击、未拖拽 → 只重置状态，不重建
        self._reorder = None
```

**结论**：`_render()` 只在拖拽完成、数据变更时调用，普通点击不能触发重建。

---

## 勾选自动排序

勾选后，已完成待办自动移到列表底部（数据数组开头）：

```python
def _toggle(self, idx):
    items[idx]["done"] = not items[idx]["done"]
    done = [it for it in items if it["done"]]
    not_done = [it for it in items if not it["done"]]
    self.todos[self.today] = done + not_done  # done 在前 → 显示在下（reversed）
```

---

## 最小化与恢复

- 点击绿色圆点 → `withdraw()` + 创建 `MiniBar`（悬浮条）
- MiniBar 显示时间 + 待办数量，可拖动，每 30 秒更新
- 双击 MiniBar → `deiconify()` + 恢复时钟更新 + 销毁 MiniBar

---

## 清空功能

Header 中日期右侧的「清空 ▾」按钮组：

- 点击「清空」→ 清空已完成待办（`_clear_done`）
- 点击「▾」→ 弹出菜单：
  - 清空已完成待办
  - 清空待办（保留已完成）
  - 清空全部

---

## 视图切换

点击黄色圆点循环切换 small → medium → large：

1. 更新 `self.sk` 和窗口 geometry
2. 保存设置到 `todo_settings.json`
3. 销毁 `self.main` 下所有子控件
4. 重建 `self.body` + header + input + list
5. 重新渲染

---

## 启动时自动继承与清理

每次启动应用时，在 `__init__` 中自动执行以下逻辑：

1. **清理历史已完成待办** — 遍历所有历史日期，删除 `done: true` 的项
2. **继承未完成待办** — 如果今天列表为空，从所有历史日期中收集未完成的待办（按日期升序），全部继承到今天
3. **删除空日期条目** — 清理后没有内容的历史日期从数据文件中移除
4. **保存** — 有变更时立即写入 `todo_data.json`

```python
# 清理已完成
for d in list(self.todos.keys()):
    if d == self.today:
        continue
    self.todos[d] = [t for t in self.todos[d] if not t.get("done")]

# 继承全部未完成
if not self.todos[self.today]:
    pending = []
    for d in sorted(self.todos.keys()):
        if d == self.today:
            continue
        pending.extend(dict(t) for t in self.todos[d])
    if pending:
        self.todos[self.today] = pending

# 删除空日期
for d in [k for k in self.todos if k != self.today and not self.todos[k]]:
    del self.todos[d]
```

---

## 待办文字换行

Label 的 `wraplength` 不硬编码，渲染后根据实际可用宽度动态计算：

```python
# 渲染完成后，遍历每行计算可用宽度
for row in self.lc.winfo_children():
    inner = row.winfo_children()[0]
    cb, lbl, dl = inner.winfo_children()[0], inner.winfo_children()[1], inner.winfo_children()[2]
    avail = inner.winfo_width() - cb.winfo_reqwidth() - dl.winfo_reqwidth() - padding
    lbl.config(wraplength=avail)
```

- 扣除复选框（`cb`）、删除按钮（`dl`）和内边距后，剩余空间全部用于文字换行
- 不同视图尺寸（small/medium/large）自动适配

---

## 已知限制

1. **卡片无圆角**：tkinter 不支持透明 canvas，所有圆角方案均有缺陷
2. **无视觉滚动条**：为保证边距对齐，移除了滚动条，仅靠滚轮滚动
3. **字体依赖**：使用 `Microsoft YaHei UI`，需 Windows 中文环境

---

## 打包命令

```bash
pyinstaller TodoWidget.spec --clean --noconfirm
```

产物位于 `dist/TodoWidget.exe`，复制到项目根目录覆盖。

### 重要：所有代码修改必须同步更新 .exe

每次对 `todo_widget.py` 进行修改后，**必须重新执行打包命令**，将最新代码编译到 `TodoWidget.exe` 中。确保用户运行的 exe 始终是最新版本。

---

## 后续可加功能参考

- [x] 双击待办修改（双击 lbl 触发 `<Double-Button-1>`，替换为 Entry 编辑）
- [x] 跨日继承未完成待办（启动时自动继承所有历史未完成项，清理已完成项）
- [ ] 多日待办切换（日期选择器）
- [ ] 待办分类/标签
- [ ] 搜索/过滤
- [ ] 导出/导入
- [ ] 快捷键支持
- [ ] 开机自启
- [ ] 深色模式
