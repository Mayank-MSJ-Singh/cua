import subprocess
import asyncio
import json
import pyautogui
import pyperclip
from PIL import Image
from io import BytesIO
import base64
import pyatspi

# Linux UI Element representation for AccessibilityHandler
class LinuxUIElement:
    """
    A representation of an accessible UI element on Linux (X11), using AT-SPI.
    Think of it as telemetry data for GUI components.
    """
    def __init__(self, accessible):
        try:
            self.role = accessible.getRoleName()
        except Exception:
            self.role = ''
        # Name or title of the element
        try:
            self.title = accessible.name or ''
        except Exception:
            self.title = ''
        # Value or text content of the element
        self.value = ''
        try:
            # Try to extract text content if available
            text_iface = accessible.queryText()
            if text_iface:
                self.value = text_iface.getText(0, -1) or ''
        except Exception:
            # No text interface; try value interface
            try:
                val_iface = accessible.queryValue()
                if val_iface:
                    self.value = str(val_iface.currentValue)
            except Exception:
                self.value = self.title  # fallback to title if nothing else

        # Coordinates and size (bounding box) of the element
        self.x = self.y = self.width = self.height = 0
        try:
            comp = accessible.queryComponent()
            if comp:
                # Get position relative to the screen
                self.x, self.y = comp.getPosition(pyatspi.XY_SCREEN)
                self.width, self.height = comp.getSize()
        except Exception:
            # Could not get component info (maybe not available on this element)
            pass

        # Recursively process child elements
        self.children = []
        try:
            for child in accessible:
                try:
                    child_elem = LinuxUIElement(child)
                    self.children.append(child_elem)
                except Exception:
                    # If any child can't be processed, skip it like a boss
                    continue
        except Exception:
            # Not iterable; no children
            pass

    def to_dict(self):
        """
        Serialize this element and its children to a dictionary.
        """
        return {
            "role": self.role,
            "title": self.title,
            "value": self.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "children": [child.to_dict() for child in self.children]
        }

    def contains_value(self, search_value):
        """
        Recursively search for a value in this element or its children (case-insensitive).
        """
        if search_value is None:
            return False
        if self.value and search_value.lower() in str(self.value).lower():
            return True
        if self.title and search_value.lower() in str(self.title).lower():
            return True
        for child in self.children:
            if child.contains_value(search_value):
                return True
        return False

class LinuxAccessibilityHandler:
    """
    Handler for Linux accessibility (X11) using AT-SPI and X11 tools.
    We'll walk through the UI tree like an intrepid explorer.
    """
    async def get_windows(self):
        """
        Get a list of top-level windows (frames/dialogs) via AT-SPI.
        Falls back to wmctrl if needed.
        """
        try:
            desktop = pyatspi.Registry.getDesktop(0)
            windows = []
            for i in range(desktop.childCount):
                app = desktop.getChildAtIndex(i)
                for j in range(app.childCount):
                    window = app.getChildAtIndex(j)
                    try:
                        role = window.getRoleName().lower()
                    except Exception:
                        role = ''
                    if role in ("frame", "window", "dialog"):
                        try:
                            ui_elem = LinuxUIElement(window)
                            windows.append(ui_elem.to_dict())
                        except Exception:
                            continue
            if not windows:
                # AT-SPI didn't find any windows; fall back to wmctrl listing
                try:
                    wm_output = subprocess.check_output(['wmctrl', '-l'], text=True)
                    for line in wm_output.splitlines():
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            _, _, _, title = parts
                            windows.append({"role": "window", "title": title.strip(),
                                            "value": "", "x": 0, "y": 0,
                                            "width": 0, "height": 0, "children": []})
                except Exception:
                    # If even wmctrl fails, return empty list
                    pass
            return {"success": True, "windows": windows}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def find_window_by_title(self, title):
        """
        Find the first window whose title contains the given string (case-insensitive).
        """
        try:
            result = await self.get_windows()
            if not result.get("success"):
                return result
            for win in result.get("windows", []):
                if title.lower() in win.get("title", "").lower():
                    return {"success": True, "window": win}
            return {"success": False, "error": f"No window with title containing '{title}' found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def find_window_by_role(self, role):
        """
        Find all windows with a given role (case-insensitive).
        """
        try:
            result = await self.get_windows()
            if not result.get("success"):
                return result
            matches = [w for w in result.get("windows", []) if w.get("role", "").lower() == role.lower()]
            if matches:
                return {"success": True, "windows": matches}
            else:
                return {"success": False, "error": f"No windows with role '{role}' found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def find_window_by_value(self, value):
        """
        Find the first window containing a UI element with the given value/text (case-insensitive).
        """
        try:
            desktop = pyatspi.Registry.getDesktop(0)
            for i in range(desktop.childCount):
                app = desktop.getChildAtIndex(i)
                for j in range(app.childCount):
                    window = app.getChildAtIndex(j)
                    try:
                        role = window.getRoleName().lower()
                    except Exception:
                        role = ''
                    if role in ("frame", "window", "dialog"):
                        ui_elem = LinuxUIElement(window)
                        if ui_elem.contains_value(value):
                            return {"success": True, "window": ui_elem.to_dict()}
            return {"success": False, "error": f"No window with value '{value}' found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

class LinuxAutomationHandler:
    """
    Handler for automating user interactions on Linux (X11).
    Pretend this is your intelligent sidekick clicking and typing on demand.
    """
    async def click(self, x, y, button='left'):
        """
        Click at (x, y) with specified mouse button.
        """
        try:
            await asyncio.to_thread(pyautogui.click, x, y, button=button)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def double_click(self, x, y):
        """
        Double-click at (x, y).
        """
        try:
            await asyncio.to_thread(pyautogui.doubleClick, x, y)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def right_click(self, x, y):
        """
        Right-click at (x, y).
        """
        try:
            await asyncio.to_thread(pyautogui.click, x, y, button='right')
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def move_to(self, x, y, duration=0.0):
        """
        Move mouse to (x, y) optionally over a duration.
        """
        try:
            await asyncio.to_thread(pyautogui.moveTo, x, y, duration=duration)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def drag_to(self, x, y, duration=0.0):
        """
        Drag mouse to (x, y) from current position.
        """
        try:
            await asyncio.to_thread(pyautogui.dragTo, x, y, duration=duration)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll(self, amount, x=None, y=None):
        """
        Scroll mouse. If x,y provided, move to that position first.
        Positive amount scrolls up, negative scrolls down.
        """
        try:
            if x is not None and y is not None:
                await asyncio.to_thread(pyautogui.moveTo, x, y)
            await asyncio.to_thread(pyautogui.scroll, amount)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type(self, text, interval=0.0):
        """
        Type text as if from keyboard, with optional interval between keys.
        """
        try:
            await asyncio.to_thread(pyautogui.write, text, interval=interval)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def press_key(self, key):
        """
        Press a single key.
        """
        try:
            await asyncio.to_thread(pyautogui.press, key)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def hotkey(self, *keys):
        """
        Press a combination of keys (e.g., ctrl, c).
        """
        try:
            await asyncio.to_thread(pyautogui.hotkey, *keys)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self, region=None):
        """
        Take a screenshot. If region is provided, capture that rectangle (left, top, width, height).
        Returns the image as a base64-encoded PNG.
        """
        try:
            if region:
                image = await asyncio.to_thread(pyautogui.screenshot, region=region)
            else:
                image = await asyncio.to_thread(pyautogui.screenshot)
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode('ascii')
            return {"success": True, "image": img_str}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_clipboard(self):
        """
        Get text content from the system clipboard.
        """
        try:
            text = pyperclip.paste()
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def set_clipboard(self, text):
        """
        Set the system clipboard to the provided text.
        """
        try:
            pyperclip.copy(text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
