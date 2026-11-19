# ⏱️ Idle Alarm Timer (Sci-Fi HUD Edition)

A lightweight, always-on-top Windows desktop utility built with Python and Tkinter that monitors mouse and keyboard activity. When input stops, it automatically initiates a **2-minute and 30-second** countdown and triggers an audio-visual alert until activity resumes or the timer is manually reset.

## ✨ Features
- **Automatic Idle Detection:** Monitors global mouse movement, clicks, scrolling, and keyboard keystrokes via `pynput`.
- **Smart Auto-Reset:** Stays at `02:30` while you are active, starts counting down the moment you go idle, and immediately silences and resets the alarm as soon as you move your mouse or press a key.
- **Custom Sci-Fi HUD Interface:** Borderless draggable window with a glowing 7-segment digital clock, dynamic status badges, and a real-time progress bar.
- **4 Built-in Synthesized Alarm Tones:** Generates clean 44.1 kHz 16-bit PCM WAV audio on the fly with zero external audio files required:
  - *Cyberpunk Pulse (Synth Arp)*
  - *Crystal Marimba (Modern)*
  - *Neon Sonar (Deep Ping)*
  - *Horizon Chime (Ambient Pad)*
- **Live Alarm Preview:** Includes a **Test Selected Alarm** button to sample tones anytime.

## 🚀 Getting Started

### Prerequisites
- Windows 10 / 11
- Python 3.10+

### Installation & Running from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/iAmJay-cmd/idle-alarm-timer.git
   cd idle-alarm-timer