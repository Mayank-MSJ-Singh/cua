# linux.py
# Linux-specific handlers for CUA
# Dependencies: wmctrl, xdotool, pyautogui, pyperclip

import subprocess
import json
from typing import Optional, List, Dict, Any
import pyautogui
import pyperclip

from .base import BaseAccessibilityHandler, BaseAutomationHandler

# Ensure pyautogui works without failsafe
pyautogui.FAILSAFE = False

class LinuxAccessibilityHandler(BaseAccessibilityHandler):
    """
    Linux implementation of accessibility handler. Uses wmctrl to list windows
    and simple title matching for "element" finding.
    """
    def get_all_windows(self) -> List[Dict[str, Any]]:
        """Return list of dicts with keys: id, title"""
        try:
            result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, check=True)
            windows = []
            for line in result.stdout.splitlines():
                parts = line.split(None, 3)
                if len(parts) < 4:
                    continue
                win_id, _, _, title = parts
                windows.append({"id": win_id, "title": title})
            return windows
        except Exception:
            return []

    async def get_accessibility_tree(self) -> Dict[str, Any]:
        """Return a basic tree of windows as accessibility tree."""
        wins = self.get_all_windows()
        return {"success": True, "windows": wins}

    async def find_element(
        self, role: Optional[str] = None, title: Optional[str] = None, value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find window by title substring."""
        try:
            all_w = self.get_all_windows()
            if title:
                matching = [w for w in all_w if title.lower() in w["title"].lower()]
            else:
                matching = all_w
            if not matching:
                return {"success": False, "error": f"No window matching '{title}'"}
            # Return first match
            return {"success": True, "element": matching[0]}
        except Exception as e:
            return {"success": False, "error": str(e)}

class LinuxAutomationHandler(BaseAutomationHandler):
    """
    Linux implementation of automation handler. Wraps pyautogui and xdotool commands.
    """
    async def left_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.click()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.rightClick()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.doubleClick()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def move_cursor(self, x: int, y: int) -> Dict[str, Any]:
        try:
            pyautogui.moveTo(x, y)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def drag_to(
        self, x: int, y: int, button: str = "left", duration: float = 0.5
    ) -> Dict[str, Any]:
        try:
            pyautogui.dragTo(x, y, button=button, duration=duration)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(self, text: str) -> Dict[str, Any]:
        try:
            pyautogui.write(text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def press_key(self, key: str) -> Dict[str, Any]:
        try:
            pyautogui.press(key)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def hotkey(self, keys: List[str]) -> Dict[str, Any]:
        try:
            pyautogui.hotkey(*keys)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll_down(self, clicks: int = 1) -> Dict[str, Any]:
        try:
            pyautogui.scroll(-clicks)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll_up(self, clicks: int = 1) -> Dict[str, Any]:
        try:
            pyautogui.scroll(clicks)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self) -> Dict[str, Any]:
        try:
            from io import BytesIO
            import base64
            from PIL import Image

            img = pyautogui.screenshot()
            buf = BytesIO()
            img.save(buf, format="PNG")
            data = base64.b64encode(buf.getvalue()).decode()
            return {"success": True, "image_data": data}
        except Exception as e:
            return {"success": False, "error": f"Screenshot error: {e}"}

    async def get_screen_size(self) -> Dict[str, Any]:
        try:
            w, h = pyautogui.size()
            return {"success": True, "size": {"width": w, "height": h}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_cursor_position(self) -> Dict[str, Any]:
        try:
            x, y = pyautogui.position()
            return {"success": True, "position": {"x": x, "y": y}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def copy_to_clipboard(self) -> Dict[str, Any]:
        try:
            content = pyperclip.paste()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def set_clipboard(self, text: str) -> Dict[str, Any]:
        try:
            pyperclip.copy(text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_command(self, command: str) -> Dict[str, Any]:
        try:
            proc = subprocess.run(command, shell=True, capture_output=True, text=True)
            return {"success": True, "stdout": proc.stdout, "stderr": proc.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}
