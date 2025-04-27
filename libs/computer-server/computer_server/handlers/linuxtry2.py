#!/usr/bin/env python3
"""
Linux-compatible implementation of the CUA project utilities.
This code replaces macOS-specific libraries (AppKit, Quartz, Accessibility API)
with Linux equivalents using pyautogui, pyperclip, xdotool, xclip, scrot, wmctrl, etc.
Designed for Ubuntu (GNOME, KDE, X11).

Dependencies:
  - Python packages: pyautogui, pyperclip
  - System tools: xdotool, wmctrl, xclip (for clipboard), scrot (for screenshots if needed)
"""
import subprocess
import time
import os
from typing import List, Optional, Tuple

try:
    import pyautogui
except ImportError:
    raise ImportError("pyautogui is required. Install with: pip install pyautogui")
try:
    import pyperclip
except ImportError:
    raise ImportError("pyperclip is required. Install with: pip install pyperclip")

pyautogui.FAILSAFE = False  # disable failsafe for automated scripts

class Screen:
    """
    Screen utilities: get size and capture screenshot.
    """
    @staticmethod
    def size() -> Tuple[int, int]:
        """
        Returns the screen width and height.
        """
        width, height = pyautogui.size()
        return width, height

    @staticmethod
    def capture(save_path: Optional[str] = None):
        """
        Capture a screenshot of the entire screen.
        If save_path is provided, saves the image to the file.
        Returns a PIL Image object.
        """
        image = pyautogui.screenshot()
        if save_path:
            image.save(save_path)
        return image

class Window:
    """
    Window management using wmctrl and xdotool.
    """
    def __init__(self, id: str, desktop: Optional[int], pid: Optional[int], host: Optional[str], title: str):
        self.id = id  # hex window ID as string (e.g. '0x04a00007')
        self.desktop = desktop
        self.pid = pid
        self.host = host
        self.title = title

    def __repr__(self):
        return f"<Window id={self.id} title={self.title!r}>"

    @staticmethod
    def list() -> List['Window']:
        """
        List all windows using wmctrl. Returns a list of Window objects.
        """
        try:
            result = subprocess.run(["wmctrl", "-l", "-p"], capture_output=True, text=True)
        except FileNotFoundError:
            raise RuntimeError("wmctrl is not installed or X server is not available.")
        windows = []
        for line in result.stdout.splitlines():
            parts = line.split(None, 4)
            # wmctrl -l -p: id, desktop, pid, host, title
            if len(parts) >= 5:
                win_id = parts[0]
                desktop = int(parts[1]) if parts[1].isdigit() else None
                pid = int(parts[2]) if parts[2].isdigit() else None
                host = parts[3]
                title = parts[4]
                windows.append(Window(win_id, desktop, pid, host, title))
        return windows

    @staticmethod
    def find(title: str) -> List['Window']:
        """
        Find windows by title (case-insensitive substring match). Returns a list of matching Window objects.
        """
        title_lower = title.lower()
        return [w for w in Window.list() if title_lower in w.title.lower()]

    @staticmethod
    def get_active() -> Optional['Window']:
        """
        Get the currently active/focused window. Returns a Window object or None.
        """
        try:
            result = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True)
            win_id_dec = result.stdout.strip()
            if not win_id_dec:
                return None
            # Convert decimal to hex string similar to wmctrl output
            try:
                win_id = hex(int(win_id_dec))
            except ValueError:
                win_id = win_id_dec
            for w in Window.list():
                if w.id == win_id or w.id == win_id_dec:
                    return w
        except FileNotFoundError:
            raise RuntimeError("xdotool is not installed or X server is not available.")
        return None

    def focus(self):
        """
        Focus/raise this window using xdotool.
        """
        try:
            win_id_int = int(self.id, 16) if self.id.startswith("0x") else int(self.id)
            subprocess.run(["xdotool", "windowactivate", str(win_id_int)])
        except Exception as e:
            print(f"Failed to focus window {self.id}: {e}")

    def close(self):
        """
        Close the window.
        """
        try:
            win_id_int = int(self.id, 16) if self.id.startswith("0x") else int(self.id)
            subprocess.run(["xdotool", "windowclose", str(win_id_int)])
        except Exception as e:
            print(f"Failed to close window {self.id}: {e}")

    def move(self, x: int, y: int):
        """
        Move the window to (x, y) on screen.
        """
        try:
            subprocess.run(["wmctrl", "-i", "-r", self.id, "-e", f"0,{x},{y},-1,-1"])
        except Exception as e:
            print(f"Failed to move window {self.id}: {e}")

    def resize(self, width: int, height: int):
        """
        Resize the window to width x height, keeping top-left corner.
        """
        try:
            subprocess.run(["wmctrl", "-i", "-r", self.id, "-e", f"0,-1,-1,{width},{height}"])
        except Exception as e:
            print(f"Failed to resize window {self.id}: {e}")

    def move_resize(self, x: int, y: int, width: int, height: int):
        """
        Move and resize the window in one call.
        """
        try:
            subprocess.run(["wmctrl", "-i", "-r", self.id, "-e", f"0,{x},{y},{width},{height}"])
        except Exception as e:
            print(f"Failed to move/resize window {self.id}: {e}")

class Mouse:
    """
    Mouse control using pyautogui.
    """
    @staticmethod
    def move_to(x: int, y: int, duration: float = 0):
        """
        Move mouse cursor to (x, y). Duration in seconds for smooth movement.
        """
        pyautogui.moveTo(x, y, duration=duration)

    @staticmethod
    def click(x: Optional[int] = None, y: Optional[int] = None,
              button: str = 'left', double: bool = False):
        """
        Click mouse. If x,y provided, move there first. Button can be 'left', 'middle', 'right'.
        Double-click if double=True.
        """
        if x is not None and y is not None:
            pyautogui.moveTo(x, y)
        if double:
            pyautogui.click(clicks=2, button=button)
        else:
            pyautogui.click(button=button)

    @staticmethod
    def scroll(amount: int):
        """
        Scroll the mouse wheel by the given amount. Positive for up, negative for down.
        """
        pyautogui.scroll(amount)

class Keyboard:
    """
    Keyboard control using pyautogui.
    """
    @staticmethod
    def type(text: str, interval: float = 0):
        """
        Type the given text string. Interval in seconds between each character.
        """
        pyautogui.write(text, interval=interval)

    @staticmethod
    def press(key: str):
        """
        Press a single key (e.g. 'enter', 'a', 'ctrl').
        """
        pyautogui.press(key)

    @staticmethod
    def hotkey(*keys: str):
        """
        Press a combination of keys (e.g. 'ctrl', 'c').
        """
        pyautogui.hotkey(*keys)

class Clipboard:
    """
    Clipboard operations using pyperclip (xclip/xsel under the hood).
    """
    @staticmethod
    def copy(text: str):
        """
        Copy text to system clipboard.
        """
        pyperclip.copy(text)

    @staticmethod
    def paste() -> str:
        """
        Paste text from system clipboard.
        """
        return pyperclip.paste()

class System:
    """
    System-level operations.
    """
    @staticmethod
    def run_command(command: str, wait: bool = True):
        """
        Run a shell command. If wait=True, wait for completion.
        """
        if wait:
            subprocess.run(command, shell=True)
        else:
            subprocess.Popen(command, shell=True)
