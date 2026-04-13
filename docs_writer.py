import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import random

from pynput.keyboard import Listener, Key
import Quartz

# ---------------------------------------------------------------------------
# Delay constants – tweak these to change how "human" the typing feels
# ---------------------------------------------------------------------------
BASE_DELAY = 0.05            # 50 ms baseline per character
DELAY_VARIANCE = 0.1        # random jitter added on top (0–80 ms)
WORD_PAUSE_CHANCE = 0.15     # 15 % chance of a longer pause after a space
WORD_PAUSE_RANGE = (0.1, 0.4)
SENTENCE_PAUSE_CHANCE = 0.80 # 80 % chance of a pause after . ! ?
SENTENCE_PAUSE_RANGE = (0.3, 1.0)
NEWLINE_PAUSE_RANGE = (0.3, 0.8)
FAST_BURST_CHANCE = 0.05     # 5 % chance of a quick burst
FAST_BURST_RANGE = (0.02, 0.04)
STARTUP_DELAY = 4            # seconds before typing starts
STOP_KEY = Key.esc           # press ESC to abort


def get_delay(char: str, prev_char: str) -> float:
    """Return a human-like delay (seconds) to wait before typing *char*."""

    # Occasional fast burst (familiar key sequences)
    if random.random() < FAST_BURST_CHANCE:
        return random.uniform(*FAST_BURST_RANGE)

    delay = BASE_DELAY + random.uniform(0, DELAY_VARIANCE)

    # Pause after a space (thinking between words)
    if prev_char == " " and random.random() < WORD_PAUSE_CHANCE:
        delay += random.uniform(*WORD_PAUSE_RANGE)

    # Longer pause after sentence-ending punctuation
    if prev_char in ".!?" and char == " " and random.random() < SENTENCE_PAUSE_CHANCE:
        delay += random.uniform(*SENTENCE_PAUSE_RANGE)

    # Pause after newline (paragraph break)
    if prev_char == "\n":
        delay += random.uniform(*NEWLINE_PAUSE_RANGE)

    return delay


# ---------------------------------------------------------------------------
# Keystroke helpers – Quartz CGEvents for reliable cross-app typing on macOS
# ---------------------------------------------------------------------------

# Map common special characters to (keycode, shift?) for CGEvent approach
_KEYCODE_MAP = {
    "\n": (36, False),   # Return
    "\t": (48, False),   # Tab
}


def _type_char(char: str):
    """Type a single character using macOS CGEvents (Quartz).

    For special keys (\n, \t) we send a keycode event.
    For everything else we use a CGEvent with Unicode string – this handles
    all characters including accented/diacritical chars without needing a
    keycode lookup table.
    """
    if char in _KEYCODE_MAP:
        keycode, shift = _KEYCODE_MAP[char]
        event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
        event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
        if shift:
            Quartz.CGEventSetFlags(event_down, Quartz.kCGEventFlagMaskShift)
            Quartz.CGEventSetFlags(event_up, Quartz.kCGEventFlagMaskShift)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
    else:
        # Use a dummy keycode (0) and set the Unicode string on the event.
        # This is the most reliable way to type arbitrary Unicode on macOS.
        event_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        event_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(event_down, len(char), char)
        Quartz.CGEventKeyboardSetUnicodeString(event_up, len(char), char)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)


# ---------------------------------------------------------------------------
# Typing engine – runs in a background thread
# ---------------------------------------------------------------------------
class TypingEngine:
    def __init__(self):
        self.stop_flag = threading.Event()

    def type_text(self, text: str, on_done):
        """Type *text* character by character, then call *on_done(stopped)*."""
        self.stop_flag.clear()

        # Countdown – check stop_flag every second
        for remaining in range(STARTUP_DELAY, 0, -1):
            if self.stop_flag.is_set():
                on_done(True)
                return
            on_done(None, countdown=remaining)
            time.sleep(1)

        on_done(None, countdown=0)  # signal: typing starts now

        prev_char = ""
        for char in text:
            if self.stop_flag.is_set():
                on_done(True)
                return

            _type_char(char)

            delay = get_delay(char, prev_char)
            prev_char = char

            # Sleep in small increments so we can react to stop quickly
            elapsed = 0.0
            while elapsed < delay:
                if self.stop_flag.is_set():
                    on_done(True)
                    return
                step = min(0.05, delay - elapsed)
                time.sleep(step)
                elapsed += step

        on_done(False)  # finished normally

    def stop(self):
        self.stop_flag.set()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class DocsWriterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Docs Writer")
        self.root.geometry("520x420")
        self.root.resizable(True, True)

        self.engine = TypingEngine()
        self._typing = False

        # --- Text area ---
        label = tk.Label(root, text="Paste your text below:", anchor="w")
        label.pack(fill="x", padx=10, pady=(10, 2))

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=18)
        self.text_area.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # --- Button row ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=(0, 4))

        self.start_btn = tk.Button(
            btn_frame, text="Start Typing", width=14, command=self._on_start
        )
        self.start_btn.pack(side="left")

        self.stop_btn = tk.Button(
            btn_frame, text="Stop", width=8, command=self._on_stop, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(6, 0))

        self.clear_btn = tk.Button(
            btn_frame, text="Clear", width=8, command=self._on_clear
        )
        self.clear_btn.pack(side="left", padx=(6, 0))

        self.status = tk.Label(btn_frame, text="Ready", anchor="w", fg="gray")
        self.status.pack(side="left", padx=(12, 0), fill="x", expand=True)

        # --- Footer ---
        footer = tk.Label(
            root, text="Press ESC to stop typing at any time", fg="gray", font=("system", 10)
        )
        footer.pack(pady=(0, 6))

        # --- Global hotkey listener (ESC to stop) ---
        self._hotkey_listener = Listener(on_press=self._on_key_press)
        self._hotkey_listener.daemon = True
        self._hotkey_listener.start()

    # -- Button callbacks --------------------------------------------------

    def _on_start(self):
        text = self.text_area.get("1.0", tk.END).rstrip("\n")
        if not text:
            self._set_status("Nothing to type!", "red")
            return

        self._typing = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.clear_btn.config(state="disabled")
        self.text_area.config(state="disabled")

        thread = threading.Thread(
            target=self.engine.type_text,
            args=(text, self._typing_callback),
            daemon=True,
        )
        thread.start()

    def _on_stop(self):
        self.engine.stop()

    def _on_clear(self):
        self.text_area.delete("1.0", tk.END)
        self._set_status("Ready", "gray")

    # -- Hotkey ------------------------------------------------------------

    def _on_key_press(self, key):
        if key == STOP_KEY and self._typing:
            self.engine.stop()

    # -- Callback from typing thread (called from bg thread!) --------------

    def _typing_callback(self, stopped=None, countdown=None):
        """Thread-safe UI update via root.after()."""
        if countdown is not None:
            if countdown > 0:
                self.root.after(0, lambda c=countdown: self._set_status(
                    f"Starting in {c}... Switch to your target window!", "orange"
                ))
            else:
                self.root.after(0, lambda: self._set_status("Typing...", "blue"))
            return

        # Typing finished or stopped
        def _finish():
            self._typing = False
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.clear_btn.config(state="normal")
            self.text_area.config(state="normal")
            if stopped:
                self._set_status("Stopped.", "red")
            else:
                self._set_status("Done!", "green")

        self.root.after(0, _finish)

    # -- Helpers -----------------------------------------------------------

    def _set_status(self, text: str, color: str = "gray"):
        self.status.config(text=text, fg=color)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = DocsWriterApp(root)
    root.mainloop()
