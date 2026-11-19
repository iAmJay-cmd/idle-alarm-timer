import ctypes
import io
import math
import os
import struct
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk
import wave
import zlib
from pynput import keyboard, mouse
import winsound

# Settings (2 minutes and 30 seconds = 150 seconds)
IDLE_LIMIT = 150

# Separate app from default python.exe taskbar group in Windows
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "nasciphcosmos.idlealarmtimer.hud.3"
    )
except Exception:
    pass


def generate_taskbar_ico(ico_path):
    """Generates a crisp 64x64 RGBA .ico file (Neon Cyan HUD Stopwatch)."""
    size = 64
    cx, cy = size / 2.0, size / 2.0
    rows = []

    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.hypot(dx, dy)
            r, g, b, a = 0, 0, 0, 0

            if 23.5 <= dist <= 29.5:
                r, g, b, a = 56, 224, 255, 255
            elif dist < 23.5:
                r, g, b, a = 12, 22, 34, 255

            if 27 <= x <= 37 and 1 <= y <= 5:
                r, g, b, a = 56, 224, 255, 255

            if 30 <= x <= 33 and 12 <= y <= 33:
                r, g, b, a = 224, 247, 255, 255
            if 31 <= x <= 47 and 30 <= y <= 33:
                r, g, b, a = 56, 224, 255, 255

            if dist <= 3.5:
                r, g, b, a = 255, 255, 255, 255

            row.extend((r, g, b, a))
        rows.append(bytes(row))

    raw_data = b"".join(rows)

    def png_chunk(chunk_type, data):
        chunk = chunk_type + data
        return (
            struct.pack("!I", len(data))
            + chunk
            + struct.pack("!I", zlib.crc32(chunk) & 0xFFFFFFFF)
        )

    ihdr = struct.pack("!IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(raw_data, 9))
        + png_chunk(b"IEND", b"")
    )

    ico_header = struct.pack("<HHH", 0, 1, 1)
    ico_entry = struct.pack(
        "<BBBBHHII", size, size, 0, 0, 1, 32, len(png_bytes), 6 + 16
    )

    with open(ico_path, "wb") as f:
        f.write(ico_header + ico_entry + png_bytes)


class ModernSynthAudio:
    """Synthesizes clean 44.1kHz 16-bit PCM WAV files in temp dir for true async playback."""

    SAMPLE_RATE = 44100

    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), "IdleAlarmTimerAudio")
        os.makedirs(self.temp_dir, exist_ok=True)

        self.tone_files = {
            "Cyberpunk Pulse (Synth Arp)": self._save_wav("cyberpunk.wav", self._build_cyberpunk_arp()),
            "Crystal Marimba (Modern)": self._save_wav("marimba.wav", self._build_crystal_marimba()),
            "Neon Sonar (Deep Ping)": self._save_wav("sonar.wav", self._build_neon_sonar()),
            "Horizon Chime (Ambient Pad)": self._save_wav("horizon.wav", self._build_horizon_chime()),
        }

    def _save_wav(self, filename, float_samples):
        filepath = os.path.join(self.temp_dir, filename)
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            pcm = bytearray()
            for s in float_samples:
                clamped = max(-1.0, min(1.0, s))
                pcm.extend(struct.pack("<h", int(clamped * 32767)))
            wf.writeframes(bytes(pcm))
        return filepath

    def _mix_note(self, buffer, start_sec, dur_sec, freq, vol=0.35, timbre="bell"):
        start_idx = int(start_sec * self.SAMPLE_RATE)
        num_samples = int(dur_sec * self.SAMPLE_RATE)
        end_idx = min(len(buffer), start_idx + num_samples)

        for i in range(start_idx, end_idx):
            t = (i - start_idx) / self.SAMPLE_RATE
            attack = min(1.0, t / 0.008)
            decay = math.exp(-t * (4.5 if timbre == "bell" else 3.0))
            env = attack * decay

            if timbre == "bell":
                sig = (
                    0.65 * math.sin(2 * math.pi * freq * t)
                    + 0.25 * math.sin(2 * math.pi * (freq * 2.0) * t) * math.exp(-t * 8.0)
                    + 0.10 * math.sin(2 * math.pi * (freq * 3.0) * t) * math.exp(-t * 14.0)
                )
            elif timbre == "synth":
                s1 = math.sin(2 * math.pi * freq * t)
                s2 = math.sin(2 * math.pi * (freq * 1.004) * t)
                sub = 0.4 * math.sin(2 * math.pi * (freq * 0.5) * t)
                sig = 0.45 * (s1 + s2) + sub
            else:
                vib = 1.0 + 0.002 * math.sin(2 * math.pi * 5.0 * t)
                sig = (
                    0.6 * math.sin(2 * math.pi * freq * vib * t)
                    + 0.4 * math.sin(2 * math.pi * (freq * 1.5) * t)
                )

            buffer[i] += sig * env * vol

    def _build_cyberpunk_arp(self):
        total_sec = 1.25
        buf = [0.0] * int(total_sec * self.SAMPLE_RATE)
        notes = [
            (0.00, 0.35, 293.66),
            (0.11, 0.35, 349.23),
            (0.22, 0.35, 440.00),
            (0.33, 0.45, 659.25),
            (0.46, 0.65, 587.33),
        ]
        for st, dur, f in notes:
            self._mix_note(buf, st, dur, f, vol=0.36, timbre="synth")
        return buf

    def _build_crystal_marimba(self):
        total_sec = 1.20
        buf = [0.0] * int(total_sec * self.SAMPLE_RATE)
        notes = [
            (0.00, 0.32, 523.25),
            (0.12, 0.32, 659.25),
            (0.24, 0.32, 783.99),
            (0.36, 0.36, 987.77),
            (0.50, 0.65, 1046.50),
        ]
        for st, dur, f in notes:
            self._mix_note(buf, st, dur, f, vol=0.42, timbre="bell")
        return buf

    def _build_neon_sonar(self):
        total_sec = 1.35
        buf = [0.0] * int(total_sec * self.SAMPLE_RATE)
        self._mix_note(buf, 0.00, 0.85, 880.00, vol=0.45, timbre="bell")
        self._mix_note(buf, 0.00, 0.85, 440.00, vol=0.25, timbre="bell")
        self._mix_note(buf, 0.28, 0.70, 880.00, vol=0.20, timbre="bell")
        self._mix_note(buf, 0.56, 0.65, 880.00, vol=0.09, timbre="bell")
        return buf

    def _build_horizon_chime(self):
        total_sec = 1.40
        buf = [0.0] * int(total_sec * self.SAMPLE_RATE)
        chord = [349.23, 440.00, 523.25, 659.25]
        for idx, f in enumerate(chord):
            self._mix_note(buf, idx * 0.06, 1.25, f, vol=0.24, timbre="pad")
        return buf

    def play_async(self, preset_name):
        wav_path = self.tone_files.get(preset_name)
        if wav_path and os.path.exists(wav_path):
            winsound.PlaySound(
                wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            )

    def stop(self):
        winsound.PlaySound(None, winsound.SND_PURGE)


def chamfer_points(x1, y1, x2, y2, cut=10):
    """Returns polygon coordinates for a sci-fi chamfered rectangle."""
    return [
        x1 + cut, y1,
        x2 - cut, y1,
        x2, y1 + cut,
        x2, y2 - cut,
        x2 - cut, y2,
        x1 + cut, y2,
        x1, y2 - cut,
        x1, y1 + cut,
    ]


class SciFiIdleTimerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("IDLE ALARM TIMER")
        self.W, self.H = 520, 410
        self.root.geometry(f"{self.W}x{self.H}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#09111a")

        # Borderless HUD frame while keeping taskbar presence
        self.root.overrideredirect(True)
        self.root.after(10, self._restore_taskbar_icon)

        self.apply_taskbar_icon()

        # Pre-render modern studio WAV tones in temp folder
        self.synth = ModernSynthAudio()

        self.last_activity = time.time()
        self.is_running = True
        self.alarm_triggered = False
        self.is_testing_sound = False
        self._drag_x = 0
        self._drag_y = 0

        # Modern Alarm Sound Presets
        self.alarm_options = list(self.synth.tone_files.keys())
        self.selected_alarm = tk.StringVar(value=self.alarm_options[0])

        # Main HUD Canvas
        self.canvas = tk.Canvas(
            root,
            width=self.W,
            height=self.H,
            bg="#09111a",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.draw_hud_chassis()
        self.build_controls()

        # Bind window dragging on top header
        self.canvas.tag_bind("header_drag", "<ButtonPress-1>", self.start_move)
        self.canvas.tag_bind("header_drag", "<B1-Motion>", self.do_move)

        # Start Mouse & Keyboard Listeners
        self.start_listeners()

        # Start Timer Loop
        self.update_timer()

    def _restore_taskbar_icon(self):
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self.root.wm_withdraw()
        self.root.after(10, self.root.wm_deiconify)

    def start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def apply_taskbar_icon(self):
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        ico_path = os.path.join(base_dir, "timer_icon.ico")
        generate_taskbar_ico(ico_path)
        self.root.iconbitmap(default=ico_path)

    def draw_hud_chassis(self):
        c = self.canvas
        W, H = self.W, self.H

        c.create_rectangle(1, 1, W - 1, H - 1, fill="#0b1521", outline="#284b6b", width=2)
        c.create_polygon(
            chamfer_points(14, 46, W - 14, H - 14, cut=16),
            fill="#0d1926",
            outline="#264b6e",
            width=2,
        )
        c.create_polygon(
            chamfer_points(20, 52, W - 20, H - 20, cut=14),
            fill="",
            outline="#162d44",
            width=1,
        )

        # Left & Right glowing cyan energy rails
        c.create_line(7, 85, 7, H - 55, fill="#195c85", width=3)
        c.create_line(7, 135, 7, H - 105, fill="#4ce2ff", width=2)
        c.create_line(W - 7, 85, W - 7, H - 55, fill="#195c85", width=3)
        c.create_line(W - 7, 135, W - 7, H - 105, fill="#4ce2ff", width=2)

        # Top Header Bar
        c.create_rectangle(2, 2, W - 2, 40, fill="#132436", outline="", tags="header_drag")
        c.create_line(2, 40, W - 2, 40, fill="#356894", width=1, tags="header_drag")
        c.create_line(140, 40, 380, 40, fill="#5ce8ff", width=2, tags="header_drag")

        # Glowing Stopwatch Vector Icon in Top-Left Header
        cx, cy = 24, 21
        c.create_oval(cx - 11, cy - 11, cx + 11, cy + 11, outline="#1c6e9c", width=3, tags="header_drag")
        c.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, outline="#5ce8ff", width=2, tags="header_drag")
        c.create_line(cx - 3, cy - 12, cx + 3, cy - 12, fill="#5ce8ff", width=2, tags="header_drag")
        c.create_line(cx, cy, cx, cy - 5, fill="#dff9ff", width=2, tags="header_drag")
        c.create_line(cx, cy, cx + 4, cy + 2, fill="#5ce8ff", width=2, tags="header_drag")

        c.create_text(
            44,
            21,
            text="IDLE ALARM TIMER",
            anchor="w",
            font=("Segoe UI", 12, "bold"),
            fill="#8be9fd",
            tags="header_drag",
        )

        for i in range(5):
            bx = W - 125 + (i * 7)
            c.create_line(bx, 10, bx + 4, 4, fill="#3b6991", width=2, tags="header_drag")

        # Minimize Button (_)
        min_btn = c.create_rectangle(W - 68, 6, W - 38, 34, fill="#132436", outline="")
        min_txt = c.create_text(W - 53, 19, text="—", font=("Segoe UI", 10, "bold"), fill="#8aa8c7")
        for tag in (min_btn, min_txt):
            c.tag_bind(tag, "<Button-1>", lambda e: self.minimize_window())
            c.tag_bind(tag, "<Enter>", lambda e: c.itemconfig(min_btn, fill="#1e3954"))
            c.tag_bind(tag, "<Leave>", lambda e: c.itemconfig(min_btn, fill="#132436"))

        # Close Button (X)
        cls_btn = c.create_rectangle(W - 34, 6, W - 6, 34, fill="#132436", outline="")
        cls_txt = c.create_text(W - 20, 20, text="✕", font=("Segoe UI", 10, "bold"), fill="#8aa8c7")
        for tag in (cls_btn, cls_txt):
            c.tag_bind(tag, "<Button-1>", lambda e: self.on_closing())
            c.tag_bind(tag, "<Enter>", lambda e: c.itemconfig(cls_btn, fill="#7a1c2e"))
            c.tag_bind(tag, "<Leave>", lambda e: c.itemconfig(cls_btn, fill="#132436"))

        # Status Badge
        self.badge_glow = c.create_polygon(
            chamfer_points(123, 62, 397, 98, cut=10),
            fill="#0d2b22",
            outline="#1e7856",
            width=4,
        )
        self.badge_box = c.create_polygon(
            chamfer_points(125, 64, 395, 96, cut=9),
            fill="#12382b",
            outline="#39e68c",
            width=2,
        )
        self.badge_text = c.create_text(
            W // 2,
            80,
            text="●  ACTIVE — AUTO-RESETTING",
            font=("Segoe UI", 11, "bold"),
            fill="#4ef59b",
        )

        # Subtitle Hint
        self.sub_text = c.create_text(
            W // 2,
            210,
            text="Activity detected. Timer stays at 02:30.",
            font=("Segoe UI", 10),
            fill="#9ab5d1",
        )

        # HUD Progress Bar
        self.bar_x1, self.bar_y1 = 46, 232
        self.bar_x2, self.bar_y2 = W - 46, 250
        self.bar_max_w = (self.bar_x2 - self.bar_x1) - 12

        self.bar_outer = c.create_polygon(
            chamfer_points(self.bar_x1, self.bar_y1, self.bar_x2, self.bar_y2, cut=6),
            fill="#0a1622",
            outline="#297055",
            width=2,
        )
        for tx in range(self.bar_x1 + 14, self.bar_x2 - 14, 8):
            c.create_line(tx, self.bar_y1 - 4, tx, self.bar_y1 - 2, fill="#244a6b", width=1)
            c.create_line(tx, self.bar_y2 + 2, tx, self.bar_y2 + 4, fill="#244a6b", width=1)

        self.bar_fill_glow = c.create_rectangle(
            self.bar_x1 + 6,
            self.bar_y1 + 4,
            self.bar_x1 + 6 + self.bar_max_w,
            self.bar_y2 - 4,
            fill="#22995d",
            outline="",
        )
        self.bar_fill = c.create_rectangle(
            self.bar_x1 + 6,
            self.bar_y1 + 5,
            self.bar_x1 + 6 + self.bar_max_w,
            self.bar_y2 - 5,
            fill="#4ef59b",
            outline="",
        )

        # Alarm Tone Label & Frame
        c.create_text(
            178,
            286,
            text="Alarm Tone:",
            anchor="e",
            font=("Segoe UI", 11, "bold"),
            fill="#7cc9eb",
        )
        c.create_polygon(
            chamfer_points(188, 269, 444, 303, cut=8),
            fill="#122336",
            outline="#386b96",
            width=2,
        )

    def draw_7seg_digit(self, x, y, digit, color, glow_color):
        patterns = {
            "0": (1, 1, 1, 1, 1, 1, 0),
            "1": (0, 1, 1, 0, 0, 0, 0),
            "2": (1, 1, 0, 1, 1, 0, 1),
            "3": (1, 1, 1, 1, 0, 0, 1),
            "4": (0, 1, 1, 0, 0, 1, 1),
            "5": (1, 0, 1, 1, 0, 1, 1),
            "6": (1, 0, 1, 1, 1, 1, 1),
            "7": (1, 1, 1, 0, 0, 0, 0),
            "8": (1, 1, 1, 1, 1, 1, 1),
            "9": (1, 1, 1, 1, 0, 1, 1),
        }
        w, h, t = 42, 74, 7
        segs = {
            0: [x + 4, y, x + w - 4, y, x + w - 8, y + t, x + 8, y + t],
            1: [x + w, y + 3, x + w, y + h // 2 - 2, x + w - t, y + h // 2 - 5, x + w - t, y + t + 2],
            2: [x + w, y + h // 2 + 2, x + w, y + h - 3, x + w - t, y + h - t - 2, x + w - t, y + h // 2 + 5],
            3: [x + 8, y + h - t, x + w - 8, y + h - t, x + w - 4, y + h, x + 4, y + h],
            4: [x, y + h // 2 + 2, x + t, y + h // 2 + 5, x + t, y + h - t - 2, x, y + h - 3],
            5: [x, y + 3, x + t, y + t + 2, x + t, y + h // 2 - 5, x, y + h // 2 - 2],
            6: [x + 5, y + h // 2, x + 9, y + h // 2 - 3, x + w - 9, y + h // 2 - 3, x + w - 5, y + h // 2, x + w - 9, y + h // 2 + 3, x + 9, y + h // 2 + 3],
        }
        active = patterns.get(digit, (0, 0, 0, 0, 0, 0, 0))
        for idx, pts in segs.items():
            if active[idx]:
                self.canvas.create_polygon(pts, fill=glow_color, outline=glow_color, width=4, tags="clock_digits")
                self.canvas.create_polygon(pts, fill=color, outline="", tags="clock_digits")
            else:
                self.canvas.create_polygon(pts, fill="#112233", outline="", tags="clock_digits")

    def render_clock(self, time_str, is_alarm=False):
        self.canvas.delete("clock_digits")
        color = "#ff6b8b" if is_alarm else "#9beeff"
        glow = "#6e192d" if is_alarm else "#1c6e96"

        start_x = 148
        y = 114
        positions = [start_x, start_x + 54, start_x + 132, start_x + 186]
        digits = [time_str[0], time_str[1], time_str[3], time_str[4]]

        for px, d in zip(positions, digits):
            self.draw_7seg_digit(px, y, d, color, glow)

        cx = start_x + 114
        for cy in (y + 22, y + 52):
            self.canvas.create_rectangle(cx - 4, cy - 4, cx + 4, cy + 4, fill=glow, outline="", tags="clock_digits")
            self.canvas.create_rectangle(cx - 2, cy - 2, cx + 2, cy + 2, fill=color, outline="", tags="clock_digits")

    def build_controls(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "HUD.TCombobox",
            fieldbackground="#122336",
            background="#1b3552",
            foreground="#d0e8ff",
            arrowcolor="#64e3ff",
            borderwidth=0,
            padding=3,
        )
        style.map(
            "HUD.TCombobox",
            fieldbackground=[("readonly", "#122336")],
            selectbackground=[("readonly", "#122336")],
            selectforeground=[("readonly", "#d0e8ff")],
        )

        self.alarm_dropdown = ttk.Combobox(
            self.root,
            textvariable=self.selected_alarm,
            values=self.alarm_options,
            state="readonly",
            width=24,
            font=("Segoe UI", 10),
            style="HUD.TCombobox",
        )
        self.canvas.create_window(316, 286, window=self.alarm_dropdown)

        # Left Button: Test Selected Alarm
        self.test_poly = self.canvas.create_polygon(
            chamfer_points(46, 326, 250, 372, cut=10),
            fill="#192342",
            outline="#5568b8",
            width=2,
        )
        self.test_label = self.canvas.create_text(
            148,
            349,
            text="🔊  Test Selected Alarm",
            font=("Segoe UI", 10, "bold"),
            fill="#d6e2ff",
        )
        for item in (self.test_poly, self.test_label):
            self.canvas.tag_bind(item, "<Button-1>", lambda e: self.test_alarm_sample())
            self.canvas.tag_bind(
                item, "<Enter>", lambda e: self.canvas.itemconfig(self.test_poly, fill="#243361", outline="#7d95f5")
            )
            self.canvas.tag_bind(
                item, "<Leave>", lambda e: self.canvas.itemconfig(self.test_poly, fill="#192342", outline="#5568b8")
            )

        # Right Button: Stop / Reset
        self.reset_poly = self.canvas.create_polygon(
            chamfer_points(270, 326, 474, 372, cut=10),
            fill="#10364f",
            outline="#42d4ff",
            width=2,
        )
        self.reset_label = self.canvas.create_text(
            372,
            349,
            text="⏹  Stop / Reset",
            font=("Segoe UI", 10, "bold"),
            fill="#e0f9ff",
        )
        for item in (self.reset_poly, self.reset_label):
            self.canvas.tag_bind(item, "<Button-1>", lambda e: self.manual_reset())
            self.canvas.tag_bind(
                item, "<Enter>", lambda e: self.canvas.itemconfig(self.reset_poly, fill="#184d70", outline="#7ee5ff")
            )
            self.canvas.tag_bind(
                item, "<Leave>", lambda e: self.canvas.itemconfig(self.reset_poly, fill="#10364f", outline="#42d4ff")
            )

        self.render_clock("02:30", is_alarm=False)

    def minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("", self._on_restore)

    def _on_restore(self, event):
        if self.root.state() == "normal":
            self.root.unbind("")
            self.root.overrideredirect(True)
            self.root.after(10, self._restore_taskbar_icon)

    def test_alarm_sample(self):
        if self.is_testing_sound or self.alarm_triggered:
            return
        self.is_testing_sound = True
        self.canvas.itemconfig(self.test_label, text="🔊  Playing Sample...", fill="#ffe58f")
        preset = self.selected_alarm.get()

        def run_sample():
            for _ in range(2):
                if not self.is_running or self.alarm_triggered:
                    break
                self.synth.play_async(preset)
                for _ in range(15):
                    if not self.is_running or self.alarm_triggered:
                        break
                    time.sleep(0.1)

            if not self.alarm_triggered:
                self.synth.stop()
            self.is_testing_sound = False
            if self.is_running:
                self.root.after(
                    0,
                    lambda: self.canvas.itemconfig(
                        self.test_label, text="🔊  Test Selected Alarm", fill="#d6e2ff"
                    ),
                )

        threading.Thread(target=run_sample, daemon=True).start()

    def on_activity(self, *args):
        self.last_activity = time.time()
        if self.alarm_triggered:
            self.alarm_triggered = False
            self.synth.stop()
            if self.is_running:
                self.root.after(0, self.manual_reset)

    def manual_reset(self):
        self.alarm_triggered = False
        self.synth.stop()
        self.last_activity = time.time()
        self.canvas.itemconfig(self.badge_glow, fill="#0d2b22", outline="#1e7856")
        self.canvas.itemconfig(self.badge_box, fill="#12382b", outline="#39e68c")
        self.canvas.itemconfig(self.badge_text, text="●  ACTIVE — AUTO-RESETTING", fill="#4ef59b")
        self.canvas.itemconfig(self.sub_text, text="Activity detected. Timer stays at 02:30.", fill="#9ab5d1")
        self.canvas.itemconfig(self.bar_outer, outline="#297055")
        self.canvas.itemconfig(self.bar_fill_glow, fill="#22995d")
        self.canvas.itemconfig(self.bar_fill, fill="#4ef59b")

    def start_listeners(self):
        self.mouse_listener = mouse.Listener(
            on_move=self.on_activity,
            on_click=self.on_activity,
            on_scroll=self.on_activity,
        )
        self.keyboard_listener = keyboard.Listener(on_press=self.on_activity)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def play_alarm_loop(self):
        while self.alarm_triggered and self.is_running:
            preset = self.selected_alarm.get()
            self.synth.play_async(preset)
            for _ in range(16):
                if not self.alarm_triggered or not self.is_running:
                    self.synth.stop()
                    return
                time.sleep(0.1)

    def update_timer(self):
        if not self.is_running:
            return

        idle_duration = time.time() - self.last_activity
        remaining = max(0, IDLE_LIMIT - idle_duration)

        mins = int(remaining // 60)
        secs = int(remaining % 60)
        time_str = f"{mins:02d}:{secs:02d}"
        self.render_clock(time_str, is_alarm=self.alarm_triggered)

        # Update Progress Bar width
        ratio = remaining / IDLE_LIMIT
        curr_w = int(self.bar_max_w * ratio)
        x_start = self.bar_x1 + 6
        self.canvas.coords(self.bar_fill_glow, x_start, self.bar_y1 + 4, x_start + curr_w, self.bar_y2 - 4)
        self.canvas.coords(self.bar_fill, x_start, self.bar_y1 + 5, x_start + curr_w, self.bar_y2 - 5)

        if idle_duration < 1.0 and not self.alarm_triggered:
            self.canvas.itemconfig(self.badge_glow, fill="#0d2b22", outline="#1e7856")
            self.canvas.itemconfig(self.badge_box, fill="#12382b", outline="#39e68c")
            self.canvas.itemconfig(self.badge_text, text="●  ACTIVE — AUTO-RESETTING", fill="#4ef59b")
            self.canvas.itemconfig(self.sub_text, text="Activity detected. Timer stays at 02:30.", fill="#9ab5d1")
            self.canvas.itemconfig(self.bar_outer, outline="#297055")
            self.canvas.itemconfig(self.bar_fill_glow, fill="#22995d")
            self.canvas.itemconfig(self.bar_fill, fill="#4ef59b")

        elif not self.alarm_triggered:
            self.canvas.itemconfig(self.badge_glow, fill="#2e240e", outline="#85651a")
            self.canvas.itemconfig(self.badge_box, fill="#3d2f11", outline="#ffcb47")
            self.canvas.itemconfig(self.badge_text, text="⏳  IDLE — COUNTING DOWN", fill="#ffd966")
            self.canvas.itemconfig(self.sub_text, text="No input detected. Move mouse to reset.", fill="#d9c382")
            self.canvas.itemconfig(self.bar_outer, outline="#85651a")
            self.canvas.itemconfig(self.bar_fill_glow, fill="#997319")
            self.canvas.itemconfig(self.bar_fill, fill="#ffcb47")

        # Trigger Alarm at 00:00
        if remaining <= 0 and not self.alarm_triggered:
            self.alarm_triggered = True
            self.canvas.itemconfig(self.badge_glow, fill="#330e17", outline="#94223b")
            self.canvas.itemconfig(self.badge_box, fill="#47121e", outline="#ff4d6d")
            self.canvas.itemconfig(self.badge_text, text="🔔  TIME'S UP! IDLE ALERT", fill="#ff758f")
            self.canvas.itemconfig(
                self.sub_text,
                text="Move mouse, press any key, or click Stop!",
                fill="#ff8fa3",
            )
            self.canvas.itemconfig(self.bar_outer, outline="#94223b")
            threading.Thread(target=self.play_alarm_loop, daemon=True).start()

        self.root.after(150, self.update_timer)

    def on_closing(self):
        self.is_running = False
        self.synth.stop()
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SciFiIdleTimerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()