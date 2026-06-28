#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paster — 模拟键盘逐字输入
绕过不允许复制粘贴的文本框 / 在线编译器
"""

import sys, subprocess, importlib, os, ctypes

REQ = {"pyperclip": "pyperclip", "keyboard": "keyboard"}

def _install():
    missing = [k for k in REQ if importlib.util.find_spec(k) is None]
    if not missing:
        return
    pkgs = [REQ[m] for m in missing]
    print("[Paster] Installing:", ", ".join(pkgs))
    args = [sys.executable, "-m", "pip", "install", "-q"]
    if sys.platform != "win32":
        args.append("--break-system-packages")
    args.extend(pkgs)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            r2 = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q"] + pkgs,
                capture_output=True, text=True, timeout=120)
            if r2.returncode != 0:
                print("[Paster] Install failed:", r2.stderr[:300])
                return
        print("[Paster] Install OK")
    except Exception as e:
        print("[Paster] Install error:", e)

try:
    _install()
except Exception:
    pass

import tkinter as tk
from tkinter import ttk, messagebox
import threading, time

try:
    import pyperclip; PYPERCLIP = True
except ImportError:
    PYPERCLIP = False

try:
    import keyboard as kb; KEYBOARD = True
except ImportError:
    KEYBOARD = False

class C:
    BG = "#0d1117"; SURFACE = "#161b22"; CARD = "#21262d"
    BORDER = "#30363d"; FG = "#e6edf3"; MUTED = "#8b949e"
    ACCENT = "#58a6ff"; ACCENT2 = "#79c0ff"
    GREEN = "#3fb950"; GREEN2 = "#56d364"
    ORANGE = "#d29922"; RED = "#f85149"; RED2 = "#ff6b6b"
    PURPLE = "#bc8cff"

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP   = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYDOWN = 0x0000

class _KI(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class _IN(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ki", _KI),
        ("padding", ctypes.c_ubyte * 8),
    ]

def _send_input_arr(arr):
    ctypes.windll.user32.SendInput(len(arr), ctypes.byref(arr), ctypes.sizeof(_IN))

def send_char(ch):
    cp = ord(ch)
    d = _IN(); u = _IN()
    d.type = INPUT_KEYBOARD; u.type = INPUT_KEYBOARD
    d.ki.wVk = 0; d.ki.wScan = cp; d.ki.dwFlags = KEYEVENTF_UNICODE
    d.ki.time = 0; d.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    u.ki.wVk = 0; u.ki.wScan = cp; u.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
    u.ki.time = 0; u.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    arr = (_IN * 2)(d, u)
    _send_input_arr(arr)

def send_vk(vk):
    d = _IN(); u = _IN()
    d.type = INPUT_KEYBOARD; u.type = INPUT_KEYBOARD
    d.ki.wVk = vk; d.ki.wScan = 0; d.ki.dwFlags = KEYEVENTF_KEYDOWN
    d.ki.time = 0; d.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    u.ki.wVk = vk; u.ki.wScan = 0; u.ki.dwFlags = KEYEVENTF_KEYUP
    u.ki.time = 0; u.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    arr = (_IN * 2)(d, u)
    _send_input_arr(arr)

VK_ENTER = 0x0D
VK_TAB   = 0x09
VK_SPACE = 0x20

class Engine:
    def __init__(self):
        self._running = False; self._paused = False; self._stopped = False
        self._mode = "text"; self._char_ms = 50; self._enter_ms = 300

    def type_text(self, text, on_prog=None, on_stat=None):
        self._running = True; self._paused = False; self._stopped = False
        if self._mode == "code":
            lines = text.split('\n')
            text = '\n'.join(line.lstrip(' \t') for line in lines)
        total = len(text); i = 0
        while i < total and not self._stopped:
            while self._paused and not self._stopped:
                time.sleep(0.05)
            if self._stopped: break
            ch = text[i]
            if ch == '\r':
                i += 1
                if i < total and text[i] == '\n': i += 1
                send_vk(VK_ENTER)
                dly = self._enter_ms if self._mode == "code" else self._char_ms
                time.sleep(dly / 1000.0)
                if on_prog: on_prog(i, total)
                continue
            if ch == '\n':
                send_vk(VK_ENTER)
                dly = self._enter_ms if self._mode == "code" else self._char_ms
                time.sleep(dly / 1000.0)
            elif ch == '\t':
                send_vk(VK_TAB)
                time.sleep(self._char_ms / 1000.0)
            elif ch == ' ':
                send_vk(VK_SPACE)
                time.sleep(self._char_ms / 1000.0)
            else:
                send_char(ch)
                time.sleep(self._char_ms / 1000.0)
            i += 1
            if on_prog: on_prog(i, total)
        self._running = False
        if on_stat: on_stat("stopped" if self._stopped else "done")

    def start(self, text, on_prog=None, on_stat=None):
        t = threading.Thread(target=self.type_text,
                             args=(text, on_prog, on_stat), daemon=True)
        t.start(); return t
    def pause(self): self._paused = True
    def resume(self): self._paused = False
    def stop(self): self._stopped = True; self._paused = False
    @property
    def running(self): return self._running
    @property
    def paused(self): return self._paused

class RB:
    def __init__(self, parent, text="", bg=C.ACCENT, fg="#ffffff",
                 hover_bg=None, radius=8, command=None,
                 font=("Microsoft YaHei", 11, "bold"),
                 padx=24, pady=10, **kw):
        self._bg = bg; self._fg = fg
        self._hover_bg = hover_bg or self._adj(bg, 0.15)
        self._disabled_bg = "#30363d"; self._disabled_fg = C.MUTED
        self._cmd = command; self._font = font
        self._padx = padx; self._pady = pady
        self._state = "normal"; self._hover = False
        self._pressed = False; self._radius = radius
        import tkinter.font as tkf
        tf = tkf.Font(font=font)
        tw = tf.measure(text); th = tf.metrics("linespace")
        w = tw + padx * 2; h = th + pady * 2
        cb = self._bg
        self._frame = tk.Frame(parent, bg=cb, bd=0, highlightthickness=0, **kw)
        self._canvas = tk.Canvas(self._frame, width=w, height=h, bg=cb,
                                 highlightthickness=0, cursor="hand2")
        self._canvas.pack()
        self._w = w; self._h = h; self._text = text
        self._canvas.bind("<Enter>", self._e_enter)
        self._canvas.bind("<Leave>", self._e_leave)
        self._canvas.bind("<Button-1>", self._e_press)
        self._canvas.bind("<ButtonRelease-1>", self._e_release)
        self._draw()
    def pack(self, **kw): self._frame.pack(**kw)
    def pack_forget(self): self._frame.pack_forget()
    @staticmethod
    def _adj(hs, amt):
        try:
            r = int(hs[1:3],16); g = int(hs[3:5],16); b = int(hs[5:7],16)
            r = max(0,min(255,int(r+(255-r)*amt)))
            g = max(0,min(255,int(g+(255-g)*amt)))
            b = max(0,min(255,int(b+(255-b)*amt)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except: return hs
    def _cur_bg(self):
        if self._state == "disabled": return self._disabled_bg
        if self._pressed: return self._adj(self._bg, -0.15)
        if self._hover: return self._hover_bg
        return self._bg
    def _cur_fg(self):
        return self._disabled_fg if self._state == "disabled" else self._fg
    def _draw(self):
        bg = self._cur_bg()
        self._frame.configure(bg=bg)
        self._canvas.configure(bg=bg)
        cv = self._canvas; cv.delete("all")
        r = self._radius; w = self._w; h = self._h
        cv.create_arc(0,0,r*2,r*2,start=90,extent=90,fill=bg,outline="")
        cv.create_arc(w-r*2,0,w,r*2,start=0,extent=90,fill=bg,outline="")
        cv.create_arc(0,h-r*2,r*2,h,start=180,extent=90,fill=bg,outline="")
        cv.create_arc(w-r*2,h-r*2,w,h,start=270,extent=90,fill=bg,outline="")
        cv.create_rectangle(r,0,w-r,h,fill=bg,outline="")
        cv.create_rectangle(0,r,w,h-r,fill=bg,outline="")
        cv.create_text(w/2,h/2,text=self._text,
                       font=self._font,fill=self._cur_fg(),anchor="center")
    def _e_enter(self, e):
        if self._state == "disabled": return
        self._hover = True; self._draw()
    def _e_leave(self, e):
        self._hover = False; self._pressed = False; self._draw()
    def _e_press(self, e):
        if self._state == "disabled": return
        self._pressed = True; self._draw()
    def _e_release(self, e):
        if self._state == "disabled": return
        self._pressed = False; self._draw()
        if self._cmd: self._cmd()
    def enable(self):
        self._state = "normal"
        self._canvas.configure(cursor="hand2"); self._draw()
    def disable(self):
        self._state = "disabled"
        self._canvas.configure(cursor="arrow"); self._draw()
    def set_text(self, t): self._text = t; self._draw()
    def set_colors(self, bg, fg="#ffffff", hbg=None):
        self._bg = bg; self._fg = fg
        self._hover_bg = hbg or self._adj(bg, 0.15); self._draw()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Paster")
        self.root.geometry("640x500")
        self.root.minsize(540, 440)
        self.root.configure(bg=C.BG)
        self.engine = Engine()
        self._ontop = True
        self.root.attributes("-topmost", True)
        self._build()
        self._hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._sync()
        self.root.after(500, self._chk_deps)
    def _F(self, p, bg=C.BG, **kw):
        return tk.Frame(p, bg=bg, bd=0, highlightthickness=0, **kw)
    def _L(self, p, t, fg=C.MUTED, bg=None, font=("Microsoft YaHei", 9), **kw):
        return tk.Label(p, text=t, fg=fg, bg=bg or C.BG, font=font, **kw)
    def _chk_deps(self):
        m = []
        if not PYPERCLIP: m.append("pyperclip")
        if not KEYBOARD: m.append("keyboard")
        if m:
            messagebox.showwarning("Deps Missing",
                f"Missing: {', '.join(m)}\n\nAuto-install attempted.\npip install {' '.join(m)}")
    def _build(self):
        top = self._F(self.root, bg=C.SURFACE); top.pack(fill="x")
        ti = self._F(top, bg=C.SURFACE)
        ti.pack(fill="x", padx=20, pady=(10, 10))
        self._L(ti, "Paster", fg=C.FG, bg=C.SURFACE,
                font=("Microsoft YaHei", 16, "bold")).pack(side="left")
        self.btn_pin = RB(ti, text="Pin: ON", bg=C.GREEN, fg="#fff", hover_bg=C.GREEN2,
            font=("Microsoft YaHei", 9), padx=12, pady=4, radius=6, command=self._pin)
        self.btn_pin.pack(side="right", padx=(0, 4))
        tk.Frame(self.root, bg=C.BORDER, height=1, bd=0).pack(fill="x")
        m = self._F(self.root, bg=C.BG)
        m.pack(fill="both", expand=True, padx=20, pady=(12, 8))
        mc = self._F(m, bg=C.CARD); mc.pack(fill="x", pady=(0, 10))
        mi = self._F(mc, bg=C.CARD); mi.pack(fill="x", padx=16, pady=10)
        self._L(mi, "Mode", fg=C.FG, bg=C.CARD,
                font=("Microsoft YaHei", 10, "bold")).pack(side="left")
        self._mode = tk.StringVar(value="text")
        self.btn_txt = RB(mi, text="Aa  Text", bg=C.ACCENT, fg="#fff", hover_bg=C.ACCENT2,
            font=("Microsoft YaHei", 10, "bold"), padx=16, pady=6, radius=6,
            command=lambda: self._sw("text"))
        self.btn_txt.pack(side="left", padx=(12, 4))
        self.btn_cod = RB(mi, text="</>  Code", bg=C.CARD, fg=C.MUTED, hover_bg=C.BORDER,
            font=("Microsoft YaHei", 10), padx=16, pady=6, radius=6,
            command=lambda: self._sw("code"))
        self.btn_cod.pack(side="left")
        self.lbl_hint = self._L(mi, "|  Type all chars as-is",
            fg=C.MUTED, bg=C.CARD, font=("Microsoft YaHei", 8))
        self.lbl_hint.pack(side="left", padx=(12, 0))
        sc = self._F(m, bg=C.CARD); sc.pack(fill="x", pady=(0, 10))
        si = self._F(sc, bg=C.CARD); si.pack(fill="x", padx=16, pady=12)
        self._L(si, "Settings", fg=C.FG, bg=C.CARD,
                font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
        row = self._F(si, bg=C.CARD); row.pack(fill="x", pady=(8, 0))
        for label, var, dflt, rng, step, w in [
            ("Char delay (ms):", "sp_d", "50", (1, 5000), 5, 6),
            ("Wait countdown (s):", "sp_w", "3", (1, 30), 1, 5),
            ("Enter extra (ms):", "sp_e", "300", (0, 5000), 50, 6),
        ]:
            g = self._F(row, bg=C.CARD); g.pack(side="left", padx=(0, 20))
            self._L(g, label, fg=C.MUTED, bg=C.CARD,
                    font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 5))
            sp = tk.Spinbox(g, from_=rng[0], to=rng[1], increment=step, width=w,
                font=("Consolas", 10), bg=C.BG, fg=C.FG, relief="flat", borderwidth=1,
                insertbackground=C.FG, highlightthickness=0, buttonbackground=C.CARD,
                readonlybackground=C.BG)
            sp.delete(0, "end"); sp.insert(0, dflt); sp.pack(side="left")
            setattr(self, var, sp)
        self._L(si, "Code mode: leading spaces skipped, extra delay after Enter",
            fg=C.MUTED, bg=C.CARD, font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(8, 0))
        cc = self._F(m, bg=C.CARD); cc.pack(fill="x", pady=(0, 10))
        ci = self._F(cc, bg=C.CARD); ci.pack(fill="x", padx=16, pady=14)
        self._L(ci, "Controls", fg=C.FG, bg=C.CARD,
                font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=(0, 10))
        br = self._F(ci, bg=C.CARD); br.pack(fill="x")
        self.btn_go = RB(br, text="Start Paste", bg=C.GREEN, fg="#fff", hover_bg=C.GREEN2,
            font=("Microsoft YaHei", 13, "bold"), padx=32, pady=12, radius=8, command=self._go_btn)
        self.btn_go.pack(side="left", padx=(0, 10))
        self.btn_pau = RB(br, text="Pause", bg=C.ORANGE, fg="#000", hover_bg="#e2b340",
            font=("Microsoft YaHei", 13, "bold"), padx=32, pady=12, radius=8, command=self._pau)
        self.btn_pau.pack(side="left", padx=(0, 10)); self.btn_pau.disable()
        self.btn_stp = RB(br, text="Stop", bg=C.RED, fg="#fff", hover_bg=C.RED2,
            font=("Microsoft YaHei", 13, "bold"), padx=32, pady=12, radius=8, command=self._stp)
        self.btn_stp.pack(side="left"); self.btn_stp.disable()
        hc = self._F(m, bg="#1a2332"); hc.pack(fill="x", pady=(0, 8))
        hi = self._F(hc, bg="#1a2332"); hi.pack(fill="x", padx=16, pady=10)
        self._L(hi, "Hotkeys", fg=C.ACCENT, bg="#1a2332",
                font=("Microsoft YaHei", 10, "bold")).pack(side="left")
        tk.Frame(hi, bg=C.BORDER, width=1, height=20, bd=0).pack(side="left", padx=12)
        self._L(hi, "Ctrl+Shift+V  Start (no wait)   |   Ctrl+Shift+P  Pause/Resume",
            fg=C.FG, bg="#1a2332", font=("Consolas", 10)).pack(side="left")
        self._L(hi, "Hotkey starts immediately, no countdown",
            fg=C.MUTED, bg="#1a2332", font=("Microsoft YaHei", 7)).pack(side="right")
        sf = self._F(self.root, bg=C.BG); sf.pack(fill="x", side="bottom")
        self.lbl_pg = self._L(sf, "", fg=C.MUTED, bg=C.BG, font=("Microsoft YaHei", 9))
        self.lbl_pg.pack(side="right", padx=16, pady=8)
        self.pb = ttk.Progressbar(sf, length=160, mode="determinate")
        self.pb.pack(side="right", pady=8, padx=(0, 4))
        self.lbl_st = self._L(sf, "Ready", fg=C.GREEN, bg=C.BG,
                              font=("Microsoft YaHei", 9, "bold"))
        self.lbl_st.pack(side="left", padx=16, pady=8)
    def _sw(self, mode):
        self._mode.set(mode)
        if mode == "code":
            self.btn_cod.set_colors(C.ACCENT, "#fff", C.ACCENT2)
            self.btn_txt.set_colors(C.CARD, C.MUTED, C.BORDER)
            self.lbl_hint.config(text="|  Skip leading spaces, extra delay after Enter")
        else:
            self.btn_txt.set_colors(C.ACCENT, "#fff", C.ACCENT2)
            self.btn_cod.set_colors(C.CARD, C.MUTED, C.BORDER)
            self.lbl_hint.config(text="|  Type all characters as-is")
        self._sync()
    def _sync(self):
        try:
            self.engine._mode = self._mode.get()
            self.engine._char_ms = int(self.sp_d.get())
            self.engine._enter_ms = int(self.sp_e.get())
        except ValueError: pass
    def _pin(self):
        self._ontop = not self._ontop
        self.root.attributes("-topmost", self._ontop)
        if self._ontop:
            self.btn_pin.set_text("Pin: ON")
            self.btn_pin.set_colors(C.GREEN, "#fff", C.GREEN2)
        else:
            self.btn_pin.set_text("Pin: OFF")
            self.btn_pin.set_colors(C.BORDER, C.FG, "#484f58")
    def _get_text(self):
        if not PYPERCLIP: return None
        try:
            t = pyperclip.paste()
            return t if t else None
        except: return None
    def _go_btn(self):
        text = self._get_text()
        if not text:
            messagebox.showwarning("Empty", "Clipboard is empty. Copy text first.")
            return
        self._sync()
        if self.engine.running:
            messagebox.showinfo("Info", "Already typing.")
            return
        try: ws = int(self.sp_w.get())
        except ValueError: ws = 3
        self.lbl_st.config(text=f"{len(text)} chars ready... {ws}s", fg=C.ORANGE)
        self._set_run(False)
        self._cd_btn(ws, text)
    def _cd_btn(self, n, text):
        if n > 0:
            self.lbl_st.config(text=f"Focus target input... {n}s")
            self.root.after(1000, self._cd_btn, n - 1, text)
        else:
            self.lbl_st.config(text="Typing...")
            self.root.update_idletasks()
            self.root.after(200, lambda: self._bg(text))
    def _go_hk(self):
        text = self._get_text()
        if not text: return
        self._sync()
        if self.engine.running: return
        self.lbl_st.config(text=f"Hotkey: {len(text)} chars starting...", fg=C.ACCENT)
        self.root.update_idletasks()
        self.root.after(50, lambda: self._bg(text))
    def _bg(self, text):
        self._set_run(True); self._sync()
        total = len(text)
        self.pb["maximum"] = total; self.pb["value"] = 0
        def pg(d, t): self.root.after(0, self._op, d, t)
        def st(m): self.root.after(0, self._os, m)
        self.engine.start(text, pg, st)
    def _op(self, done, total):
        self.pb["value"] = done; self.lbl_pg.config(text=f"{done} / {total}")
        self.lbl_st.config(text="Typing...", fg=C.ACCENT)
    def _os(self, msg):
        if msg == "done":
            self.lbl_st.config(text="Done", fg=C.GREEN)
            self._set_run(False); self.pb["value"] = 0; self.lbl_pg.config(text="")
        elif msg == "stopped":
            self.lbl_st.config(text="Stopped", fg=C.RED)
            self._set_run(False); self.pb["value"] = 0; self.lbl_pg.config(text="")
    def _set_run(self, running):
        if running:
            self.btn_go.set_text("Running...")
            self.btn_go.set_colors(C.BORDER, C.MUTED, "#484f58"); self.btn_go.disable()
            self.btn_pau.enable(); self.btn_stp.enable()
        else:
            self.btn_go.set_text("Start Paste")
            self.btn_go.set_colors(C.GREEN, "#fff", C.GREEN2); self.btn_go.enable()
            self.btn_pau.set_text("Pause"); self.btn_pau.disable()
            self.btn_stp.disable()
    def _pau(self):
        if self.engine.paused:
            self.engine.resume()
            self.btn_pau.set_text("Pause")
            self.lbl_st.config(text="Resumed...", fg=C.ACCENT)
        else:
            self.engine.pause()
            self.btn_pau.set_text("Resume")
            self.lbl_st.config(text="Paused", fg=C.ORANGE)
    def _stp(self):
        if self.engine.running:
            self.engine.stop()
            self.lbl_st.config(text="Stopping...", fg=C.RED)
    def _hotkeys(self):
        if not KEYBOARD: return
        try:
            kb.add_hotkey("ctrl+shift+v", self._go_hk, suppress=True)
            kb.add_hotkey("ctrl+shift+p", self._pau, suppress=True)
        except Exception as e:
            print(f"[Paster] Hotkey error: {e}")
    def _unhk(self):
        if KEYBOARD:
            try: kb.unhook_all()
            except: pass
    def _on_close(self):
        if self.engine.running: self.engine.stop()
        self._unhk(); self.root.destroy()

def main():
    print("[Paster] Starting...")
    try:
        root = tk.Tk()
        App(root)
        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("Paster Error",
                f"Startup failed:\n\n{e}\n\nCheck Python installation.")
        except: pass
        sys.exit(1)

if __name__ == "__main__":
    main()
