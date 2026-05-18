import tkinter as tk
from tkinter import font as tkfont
import json
import os
from datetime import datetime

import sys

_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
DATA_FILE = os.path.join(_DIR, "todo_data.json")
SETTINGS_FILE = os.path.join(_DIR, "todo_settings.json")


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return {}


def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── palette ──
BG     = "#F2F2F7"
CARD   = "#FFFFFF"
BORDER = "#E5E5EA"
BLACK  = "#1D1D1F"
GRAY   = "#8E8E93"
LIGHT  = "#AEAEB2"
BLUE   = "#007AFF"
GREEN  = "#34C759"
RED    = "#FF3B30"
YELLOW = "#FF9500"

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

SIZES = {"small": (260, 409), "medium": (340, 534), "large": (420, 660)}
SKEYS = ["small", "medium", "large"]
BW = SIZES["large"][0]


def _sc(w):
    return w / BW

def _si(w, v):
    return max(1, round(v * _sc(w)))


class MiniBar(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.88)
        self.configure(bg=BG)
        w = parent._sw()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        bw, bh = _si(w, 150), _si(w, 36)
        self.geometry(f"{bw}x{bh}+{sw-bw-30}+{sh-bh-60}")
        self.cv = tk.Canvas(self, width=bw, height=bh, bg=BG,
                            highlightthickness=0, cursor="hand2")
        self.cv.pack()
        r = bh // 2
        self.cv.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=CARD, outline="")
        self.cv.create_arc(bw-2*r, 0, bw, 2*r, start=0, extent=90, fill=CARD, outline="")
        self.cv.create_rectangle(r, 0, bw-r, bh, fill=CARD, outline="")
        self._t = self.cv.create_text(bw//2, bh//2, text="", fill=GRAY,
                                       font=("Microsoft YaHei UI", _si(w, 11)))
        self.cv.bind("<Button-1>", self._sd)
        self.cv.bind("<B1-Motion>", self._dd)
        self.cv.bind("<Double-Button-1>", lambda e: self._back())
        self._tick()

    def _tick(self):
        try:
            n = datetime.now().strftime("%H:%M")
            c = len(self.parent.todos.get(self.parent.today, []))
            self.cv.itemconfig(self._t, text=f"{n}  ·  {c}项待办")
            self.after(30000, self._tick)
        except tk.TclError:
            pass

    def _sd(self, e):
        self._dx, self._dy = e.x, e.y
    def _dd(self, e):
        self.geometry(f"+{self.winfo_x()+e.x-self._dx}+{self.winfo_y()+e.y-self._dy}")

    def _back(self):
        p = self.parent
        p.overrideredirect(False)
        p.deiconify()
        p.overrideredirect(True)
        p.attributes("-topmost", True)
        p.attributes("-alpha", 0.97)
        p._minimized = False
        p._tick_clock()
        self.destroy()


class TodoWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("待办")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.97)
        self.configure(bg=BG)
        self._minimized = False
        self._mini = None

        s = _load(SETTINGS_FILE)
        self.sk = s.get("size", "medium")
        if self.sk not in SIZES:
            self.sk = "medium"
        p = self._p()
        self.geometry(f"{p['w']}x{p['h']}+"
                      f"{s.get('x', self.winfo_screenwidth()-p['w']-40)}+"
                      f"{s.get('y', 40)}")

        self.todos = _load(DATA_FILE)
        now = datetime.now()
        self.today = now.strftime("%Y-%m-%d")
        self.month, self.day = now.month, now.day
        self.wday = WEEKDAYS[now.weekday()]
        if self.today not in self.todos:
            self.todos[self.today] = []
        self._drag = None
        self._reorder = None  # (index, y_root, started)
        self._editing = None

        self.bg = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.bg.pack(fill=tk.BOTH, expand=True)
        self.bg.bind("<Configure>", self._on_resize)
        self.bg.bind("<Button-1>", self._start_drag)
        self.bg.bind("<B1-Motion>", self._do_drag)

        p = self._p()
        self.main = tk.Frame(self.bg, bg=BG)
        self._mid = self.bg.create_window(p["m"], p["m"], window=self.main, anchor="nw")

        self._build_header()
        # body holds input + list + scrollbar with shared margins
        self.body = tk.Frame(self.main, bg=BG)
        self.body.pack(fill=tk.BOTH, expand=True)
        self.body.bind("<Button-1>", self._start_drag)
        self.body.bind("<B1-Motion>", self._do_drag)
        self._build_input()
        self._build_list()
        self._render()

    def _sw(self):
        return SIZES[self.sk][0]

    def _p(self):
        return {
            "w": SIZES[self.sk][0], "h": SIZES[self.sk][1],
            "m": _si(self._sw(), 14),
            "fs_t": _si(self._sw(), 18), "fs_i": _si(self._sw(), 15),
            "fs_c": _si(self._sw(), 11), "fs_in": _si(self._sw(), 14),
            "cb": _si(self._sw(), 24),
        }

    # ── rounded bg ──
    def _draw_bg(self, w, h):
        p = self._p()
        r = p["m"]
        cv = self.bg
        cv.delete("bg")
        def rr(x, y, ww, hh):
            if ww < 2*r or hh < 2*r:
                return
            cv.create_arc(x, y, x+2*r, y+2*r, start=90, extent=90, fill=BG, outline="", tags="bg")
            cv.create_arc(x+ww-2*r, y, x+ww, y+2*r, start=0, extent=90, fill=BG, outline="", tags="bg")
            cv.create_arc(x, y+hh-2*r, x+2*r, y+hh, start=180, extent=90, fill=BG, outline="", tags="bg")
            cv.create_arc(x+ww-2*r, y+hh-2*r, x+ww, y+hh, start=270, extent=90, fill=BG, outline="", tags="bg")
            cv.create_rectangle(x+r, y, x+ww-r, y+hh, fill=BG, outline="", tags="bg")
            cv.create_rectangle(x, y+r, x+ww, y+hh-r, fill=BG, outline="", tags="bg")
        rr(0, 0, w, h)

    def _on_resize(self, e):
        p = self._p()
        self._draw_bg(e.width, e.height)
        iw, ih = e.width - 2*p["m"], e.height - 2*p["m"]
        self.bg.coords(self._mid, p["m"], p["m"])
        self.bg.itemconfig(self._mid, width=iw, height=ih)

    # ── drag ──
    def _start_drag(self, e):
        self._drag = (e.x_root - self.winfo_x(), e.y_root - self.winfo_y())
    def _do_drag(self, e):
        if self._drag:
            self.geometry(f"+{e.x_root-self._drag[0]}+{e.y_root-self._drag[1]}")

    # ── reorder items ──
    def _item_press(self, e, idx):
        self._reorder = {"idx": idx, "y0": e.y_root, "started": False,
                          "widget": None, "wy0": 0, "target": idx}

    def _item_motion(self, e, idx):
        r = self._reorder
        if not r:
            return
        if not r["started"]:
            if abs(e.y_root - r["y0"]) < 8:
                return
            # start dragging
            r["started"] = True
            self.attributes("-alpha", 0.85)
            ch = self.lc.winfo_children()
            # find the visual widget for this data index
            items = self.todos.get(self.today, [])
            vis = len(items) - 1 - r["idx"]
            if vis < len(ch):
                w = ch[vis]
                r["widget"] = w
                r["wy0"] = w.winfo_rooty()
                w.configure(bg="#E8F0FE")
                w.lift()
        if not r["started"]:
            return
        # move the widget with the mouse
        dy = e.y_root - r["y0"]
        if r["widget"]:
            r["widget"].place(in_=self.lc, x=0, y=r["wy0"] - self.lc.winfo_rooty() + dy,
                              relwidth=1.0)
            r["widget"].lift()
        # compute target visual position
        ch = self.lc.winfo_children()
        if not ch:
            return
        first_y = ch[0].winfo_rooty()
        row_h = ch[0].winfo_height() + _si(self._sw(), 4)
        if row_h <= 0 or first_y <= 0:
            return
        items = self.todos.get(self.today, [])
        tv = int((e.y_root - first_y) / row_h)
        tv = max(0, min(len(items) - 1, tv))
        r["target"] = len(items) - 1 - tv

    def _item_release(self, e):
        r = self._reorder
        if not r:
            return
        if r["started"]:
            self.attributes("-alpha", 0.97)
            items = self.todos.get(self.today, [])
            src = r["idx"]
            dst = r["target"]
            if src != dst and 0 <= src < len(items) and 0 <= dst < len(items):
                item = items.pop(src)
                items.insert(dst, item)
                self._save_data()
            self._reorder = None
            self._render()
        else:
            self._reorder = None

    # ── build ──
    def _build_header(self):
        p = self._p()
        hdr = tk.Frame(self.main, bg=BG)
        hdr.pack(fill=tk.X, padx=p["m"], pady=(p["m"], 0))
        hdr.bind("<Button-1>", self._start_drag)
        hdr.bind("<B1-Motion>", self._do_drag)

        ds = _si(self._sw(), 12)
        for color, cmd in [(RED, self._close), (YELLOW, self._cycle), (GREEN, self._min)]:
            d = tk.Canvas(hdr, width=ds, height=ds, bg=BG, highlightthickness=0, cursor="hand2")
            d.create_oval(1, 1, ds-1, ds-1, fill=color, outline="")
            d.pack(side=tk.LEFT, padx=_si(self._sw(), 3))
            d.bind("<Button-1>", lambda e, c=cmd: c())

        tf = tkfont.Font(family="Microsoft YaHei UI", size=p["fs_t"], weight="bold")
        cf = tkfont.Font(family="Microsoft YaHei UI", size=p["fs_c"])
        tk.Label(hdr, text="待办", bg=BG, fg=BLACK, font=tf
                 ).pack(side=tk.LEFT, padx=(p["m"], 0))
        tk.Label(hdr, text=f"{self.month}月{self.day}日 {self.wday}",
                 bg=BG, fg=LIGHT, font=cf
                 ).pack(side=tk.LEFT, padx=(_si(self._sw(), 6), 0))

        # clear button with dropdown
        clr = tk.Frame(hdr, bg=BG)
        clr.pack(side=tk.LEFT, padx=(_si(self._sw(), 10), 0))
        bf = tkfont.Font(family="Microsoft YaHei UI", size=p["fs_c"])
        cl = tk.Label(clr, text="清空", bg=BG, fg=BLUE, font=bf, cursor="hand2")
        cl.pack(side=tk.LEFT)
        cl.bind("<Button-1>", lambda e: self._clear_done())
        arr = tk.Label(clr, text=" ▾", bg=BG, fg=GRAY, font=bf, cursor="hand2")
        arr.pack(side=tk.LEFT)
        arr.bind("<Button-1>", self._show_clear_menu)

        self.clk = tk.Label(hdr, text=datetime.now().strftime("%H:%M"),
                            bg=BG, fg=GRAY, font=("Consolas", p["fs_c"], "bold"), anchor="e")
        self.clk.pack(side=tk.RIGHT)
        self._tick_clock()

    def _build_input(self):
        p = self._p()
        bar = tk.Frame(self.body, bg=CARD, padx=p["m"]//2, pady=_si(self._sw(), 6))
        bar.pack(fill=tk.X, padx=p["m"], pady=(p["m"]//2, 0))

        bf = tkfont.Font(family="Segoe UI", size=p["fs_in"]+4, weight="bold")
        self.btn = tk.Label(bar, text="+", bg=CARD, fg=BLUE, font=bf,
                            cursor="hand2", padx=_si(self._sw(), 4))
        self.btn.pack(side=tk.LEFT)
        self.btn.bind("<Button-1>", lambda e: self._add())
        self.btn.bind("<Enter>", lambda e: self.btn.config(fg="#0056CC"))
        self.btn.bind("<Leave>", lambda e: self.btn.config(fg=BLUE))

        self.ent = tk.Entry(bar, bg=CARD, fg=BLACK, insertbackground=BLUE,
                            font=("Microsoft YaHei UI", p["fs_in"]), relief="flat", bd=0)
        self.ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=_si(self._sw(), 8),
                      padx=(_si(self._sw(), 4), 0))
        self.ent.bind("<Return>", lambda e: self._add())

        self._ph = "添加新的待办事项..."
        self.ent.bind("<FocusIn>", self._phi)
        self.ent.bind("<FocusOut>", self._pho)
        self._showph()

    def _build_list(self):
        p = self._p()
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True, padx=p["m"], pady=p["m"]//2)

        self._lc_cv = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0)
        self._lc_cv.bind("<Button-1>", self._start_drag)
        self._lc_cv.bind("<B1-Motion>", self._do_drag)
        self._lc_cv.pack(fill=tk.BOTH, expand=True)

        self.lc = tk.Frame(self._lc_cv, bg=BG)
        self._lc_win = self._lc_cv.create_window(0, 0, window=self.lc, anchor="nw")
        self.lc.bind("<Configure>",
                     lambda e: self._lc_cv.config(scrollregion=self._lc_cv.bbox("all")))
        self._lc_cv.bind("<Configure>",
                         lambda e: self._lc_cv.itemconfig(self._lc_win, width=e.width))
        self.bind_all("<MouseWheel>", self._on_wheel)

    def _on_wheel(self, e):
        x, y = self._lc_cv.winfo_rootx(), self._lc_cv.winfo_rooty()
        w, h = self._lc_cv.winfo_width(), self._lc_cv.winfo_height()
        if x <= e.x_root <= x + w and y <= e.y_root <= y + h:
            sr = self._lc_cv.cget("scrollregion").split()
            if len(sr) == 4 and int(sr[3]) > h:
                self._lc_cv.yview_scroll(int(-1 * (e.delta / 120)), "units")

    # ── clear ──
    def _clear_done(self):
        items = self.todos.get(self.today, [])
        self.todos[self.today] = [it for it in items if not it["done"]]
        self._save_data()
        self._render()

    def _clear_all(self):
        self.todos[self.today] = []
        self._save_data()
        self._render()

    def _clear_undone(self):
        items = self.todos.get(self.today, [])
        self.todos[self.today] = [it for it in items if it["done"]]
        self._save_data()
        self._render()

    def _show_clear_menu(self, e):
        m = tk.Menu(self, tearoff=0, font=("Microsoft YaHei UI", _si(self._sw(), 11)))
        m.add_command(label="清空已完成待办", command=self._clear_done)
        m.add_command(label="清空待办", command=self._clear_undone)
        m.add_command(label="清空全部", command=self._clear_all)
        m.tk_popup(e.x_root, e.y_root)

    # ── size / close / min ──
    def _cycle(self):
        i = SKEYS.index(self.sk)
        self.sk = SKEYS[(i+1)%3]
        p = self._p()
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(f"{p['w']}x{p['h']}+{x}+{y}")
        _save(SETTINGS_FILE, {"size": self.sk, "x": x, "y": y})
        self.update_idletasks()
        for w in self.main.winfo_children():
            w.destroy()
        self._build_header()
        self.body = tk.Frame(self.main, bg=BG)
        self.body.pack(fill=tk.BOTH, expand=True)
        self.body.bind("<Button-1>", self._start_drag)
        self.body.bind("<B1-Motion>", self._do_drag)
        self._build_input()
        self._build_list()
        self._render()

    def _min(self):
        self._minimized = True
        self.withdraw()
        if not self._mini or not self._mini.winfo_exists():
            self._mini = MiniBar(self)

    def _close(self):
        try:
            dates = sorted(self.todos.keys(), reverse=True)
            for d in dates[30:]:
                del self.todos[d]
            _save(DATA_FILE, self.todos)
            _save(SETTINGS_FILE, {"size": self.sk, "x": self.winfo_x(), "y": self.winfo_y()})
        except Exception:
            pass
        self.destroy()

    def _tick_clock(self):
        if self._minimized:
            return
        try:
            self.clk.config(text=datetime.now().strftime("%H:%M"))
        except (tk.TclError, AttributeError):
            return
        self.after(1000, self._tick_clock)

    # ── placeholder ──
    def _showph(self):
        if not self.ent.get():
            self.ent.insert(0, self._ph)
            self.ent.config(fg=LIGHT)
    def _phi(self, e):
        if self.ent.get() == self._ph and self.ent.cget("fg") == LIGHT:
            self.ent.delete(0, tk.END)
            self.ent.config(fg=BLACK)
    def _pho(self, e):
        if not self.ent.get().strip():
            self._showph()

    # ── operations ──
    def _add(self):
        t = self.ent.get().strip()
        if not t or t == self._ph:
            return
        self.ent.delete(0, tk.END)
        self._showph()
        self.todos[self.today].append({"text": t, "done": False})
        self._save_data()
        self._render()

    def _toggle(self, idx):
        items = self.todos.get(self.today, [])
        if 0 <= idx < len(items):
            items[idx]["done"] = not items[idx]["done"]
            done = [it for it in items if it["done"]]
            not_done = [it for it in items if not it["done"]]
            self.todos[self.today] = done + not_done
            self._save_data()
            self._render()

    def _del(self, idx):
        del self.todos[self.today][idx]
        self._save_data()
        self._render()

    # ── inline edit ──
    def _edit_start(self, idx):
        items = self.todos.get(self.today, [])
        if idx < 0 or idx >= len(items):
            return
        if self._editing is not None:
            old = self._editing
            self._editing = None
            old.unbind("<FocusOut>")
        vis = len(items) - 1 - idx
        rows = self.lc.winfo_children()
        if vis >= len(rows):
            return
        inner = rows[vis].winfo_children()[0]
        children = inner.winfo_children()
        lbl = children[1]  # cb, lbl, dl
        txt = items[idx]["text"]
        done = items[idx].get("done", False)
        p = self._p()
        fs = p["fs_i"]
        fn = tkfont.Font(family="Microsoft YaHei UI", size=fs)
        fd = tkfont.Font(family="Microsoft YaHei UI", size=fs, overstrike=True)
        lbl.pack_forget()
        ent = tk.Entry(inner, bg=CARD, fg=LIGHT if done else BLACK,
                       font=fd if done else fn, relief=tk.FLAT,
                       insertbackground=BLACK, highlightthickness=0)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ent.insert(0, txt)
        ent.select_range(0, tk.END)
        ent.focus_set()
        ent.bind("<Return>", lambda e, i=idx, en=ent: self._edit_save(i, en))
        ent.bind("<Escape>", lambda e: self._edit_cancel())
        ent.bind("<FocusOut>", lambda e, i=idx, en=ent: self._edit_save(i, en))
        self._editing = ent

    def _edit_save(self, idx, entry):
        if self._editing is None:
            return
        t = entry.get().strip()
        self._editing = None
        if not t:
            self._render()
            return
        items = self.todos.get(self.today, [])
        if 0 <= idx < len(items):
            items[idx]["text"] = t
            self._save_data()
        self._render()

    def _edit_cancel(self):
        if self._editing is None:
            return
        self._editing = None
        self._render()

    def _save_data(self):
        dates = sorted(self.todos.keys(), reverse=True)
        for d in dates[30:]:
            del self.todos[d]
        _save(DATA_FILE, self.todos)

    # ── render ──
    def _render(self):
        for w in self.lc.winfo_children():
            w.destroy()
        items = self.todos.get(self.today, [])
        p = self._p()
        fs = p["fs_i"]

        if not items:
            tk.Label(self.lc, text="暂无待办", bg=BG, fg=LIGHT,
                     font=("Microsoft YaHei UI", fs+2)).place(relx=0.5, rely=0.5, anchor="center")
            return

        fn = tkfont.Font(family="Microsoft YaHei UI", size=fs)
        fd = tkfont.Font(family="Microsoft YaHei UI", size=fs, overstrike=True)

        for i, item in enumerate(reversed(items)):
            real_idx = len(items) - 1 - i
            done = item.get("done", False)
            txt = item.get("text", "")

            row = tk.Frame(self.lc, bg=CARD)
            row.pack(fill=tk.X, pady=(0, p["m"]//2))
            row.bind("<Button-1>", lambda e, idx=real_idx: self._item_press(e, idx))
            row.bind("<B1-Motion>", lambda e, idx=real_idx: self._item_motion(e, idx))
            row.bind("<ButtonRelease-1>", self._item_release)

            inner = tk.Frame(row, bg=CARD, padx=p["m"]//2, pady=_si(self._sw(), 8))
            inner.pack(fill=tk.X)
            inner.bind("<Button-1>", lambda e, idx=real_idx: self._item_press(e, idx))
            inner.bind("<B1-Motion>", lambda e, idx=real_idx: self._item_motion(e, idx))
            inner.bind("<ButtonRelease-1>", self._item_release)

            cb = tk.Canvas(inner, width=p["cb"], height=p["cb"], bg=CARD, highlightthickness=0)
            cb.pack(side=tk.LEFT, padx=(0, _si(self._sw(), 8)))
            sz = p["cb"]
            c, rv = sz/2, sz/2-1
            if done:
                cb.create_oval(c-rv, c-rv, c+rv, c+rv, fill=GREEN, outline="")
                cb.create_line(c-rv*.38, c+.5, c-rv*.05, c+rv*.38,
                               c+rv*.45, c-rv*.32, fill="white", width=2,
                               capstyle="round", joinstyle="round")
            else:
                cb.create_oval(c-rv, c-rv, c+rv, c+rv, outline=BORDER, width=1.5)
            cb.bind("<Button-1>", lambda e, idx=real_idx: self._toggle(idx))
            cb.bind("<B1-Motion>", lambda e, idx=real_idx: self._item_motion(e, idx))
            cb.bind("<ButtonRelease-1>", self._item_release)
            cb.bind("<ButtonPress-1>", lambda e, idx=real_idx: self._item_press(e, idx), add="+")

            lbl = tk.Label(inner, text=txt, bg=CARD,
                     fg=LIGHT if done else BLACK,
                     font=fd if done else fn,
                     anchor="w", wraplength=200)
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            lbl.bind("<B1-Motion>", lambda e, idx=real_idx: self._item_motion(e, idx))
            lbl.bind("<ButtonRelease-1>", self._item_release)
            lbl.bind("<ButtonPress-1>", lambda e, idx=real_idx: self._item_press(e, idx), add="+")
            lbl.bind("<Double-Button-1>", lambda e, idx=real_idx: self._edit_start(idx))

            dl = tk.Label(inner, text="×", bg=CARD, fg=CARD,
                          font=("Segoe UI", max(fs, 12)), cursor="hand2")
            dl.pack(side=tk.RIGHT)
            dl.bind("<Button-1>", lambda e, idx=real_idx: self._del(idx))
            dl.bind("<B1-Motion>", lambda e, idx=real_idx: self._item_motion(e, idx))
            dl.bind("<ButtonRelease-1>", self._item_release)
            dl.bind("<ButtonPress-1>", lambda e, idx=real_idx: self._item_press(e, idx), add="+")

            def enter(e, lbl=dl): lbl.config(fg=GRAY)
            def leave(e, lbl=dl): lbl.config(fg=CARD)
            for w in [inner, cb] + list(inner.winfo_children()):
                w.bind("<Enter>", enter, add="+")
                w.bind("<Leave>", leave, add="+")

        self.update_idletasks()
        self._lc_cv.config(scrollregion=self._lc_cv.bbox("all"))


if __name__ == "__main__":
    app = TodoWidget()
    app.mainloop()
