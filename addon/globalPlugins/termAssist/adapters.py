# TermAssist — terminal adapters
# Each adapter knows how to read lines from one family of terminal programs.
# Author: Peera Pilarit
import ctypes

import controlTypes
import textInfos
from logHandler import log
from NVDAObjects.behaviors import Terminal

PUTTY_APPS = {"putty", "kitty", "kitty_portable", "kitty_nocompress", "puttytel", "putty-ng", "puttyng"}
PUTTY_CLASSES = {"PuTTY", "KiTTY"}
WINDOWS_TERMINAL_APPS = {"windowsterminal", "openconsole"}


def _splitLines(text, maxLines):
	text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
	lines = [l.rstrip() for l in text.split("\n")]
	while lines and not lines[-1]:
		lines.pop()
	return lines[-maxLines:]


def dedentMargin(lines):
	"""PuTTY's display model gives every line a one-space left margin. Remove it when all lines have it."""
	body = [l for l in lines if l.strip()]
	if body and all(l.startswith(" ") for l in body):
		return [l[1:] if l.startswith(" ") else l for l in lines]
	return lines


class BaseAdapter:
	kind = "generic"
	label = "Terminal"
	supportsTypeMethod = False

	def __init__(self, obj):
		self.obj = obj
		self.hwnd = getattr(obj, "windowHandle", 0) or 0
		try:
			self.appName = obj.appModule.appName
		except Exception:
			self.appName = ""

	def _allText(self):
		return self.obj.makeTextInfo(textInfos.POSITION_ALL).text

	def getLines(self, maxLines=200):
		return _splitLines(self._allText(), maxLines)

	def getCaretLine(self):
		try:
			ti = self.obj.makeTextInfo(textInfos.POSITION_CARET)
			ti.expand(textInfos.UNIT_LINE)
			t = (ti.text or "").rstrip("\r\n").rstrip()
			if t:
				return t
		except Exception:
			log.debugWarning("TermAssist: caret line failed", exc_info=True)
		lines = self.getLines(50)
		return lines[-1] if lines else ""

	def isAlive(self):
		return bool(self.hwnd) and bool(ctypes.windll.user32.IsWindow(self.hwnd))


class PuttyAdapter(BaseAdapter):
	"""PuTTY family — text comes from NVDA's display model."""
	kind = "putty"
	label = "PuTTY"
	supportsTypeMethod = True

	def __init__(self, obj):
		super().__init__(obj)
		if self.appName.lower().startswith("kitty"):
			self.label = "KiTTY"
		self._margin = False

	def getLines(self, maxLines=200):
		lines = super().getLines(maxLines)
		out = dedentMargin(lines)
		self._margin = out is not lines
		return out

	def getCaretLine(self):
		t = super().getCaretLine()
		if self._margin and t.startswith(" "):
			t = t[1:]
		return t


class UIATerminalAdapter(BaseAdapter):
	"""Windows Terminal and Windows console (conhost) through UI Automation.
	Reads only the visible lines to stay fast with a large scroll-back buffer."""
	kind = "uia"
	label = "Windows Console"

	def __init__(self, obj):
		super().__init__(obj)
		if self.appName.lower() in WINDOWS_TERMINAL_APPS:
			self.label = "Windows Terminal"

	def getLines(self, maxLines=200):
		try:
			ranges = self.obj.UIATextPattern.GetVisibleRanges()
			parts = [ranges.GetElement(i).GetText(-1) for i in range(ranges.length)]
			text = "\n".join(p.rstrip("\r\n") for p in parts)
			if text.strip():
				return _splitLines(text, maxLines)
		except Exception:
			log.debugWarning("TermAssist: visible ranges failed, falling back", exc_info=True)
		return super().getLines(maxLines)


class DisplayModelAdapter(BaseAdapter):
	"""Experimental: terminals NVDA does not know (e.g. MobaXterm). Reads text drawn on screen."""
	kind = "displayModel"
	label = "Terminal (experimental)"
	supportsTypeMethod = True

	def __init__(self, obj):
		super().__init__(obj)
		self.label = f"{self.appName} (experimental)"

	def _allText(self):
		import displayModel
		return displayModel.DisplayModelTextInfo(self.obj, textInfos.POSITION_ALL).text

	def getCaretLine(self):
		try:
			import displayModel
			ti = displayModel.DisplayModelTextInfo(self.obj, textInfos.POSITION_CARET)
			ti.expand(textInfos.UNIT_LINE)
			t = (ti.text or "").rstrip()
			if t:
				return t
		except Exception:
			pass
		lines = self.getLines(50)
		return lines[-1] if lines else ""


_GENERIC_ROLES = ("PANE", "WINDOW", "CLIENT", "UNKNOWN", "TERMINAL", "EDITABLETEXT")


def _isGenericSurface(obj):
	try:
		return obj.role in [getattr(controlTypes.Role, r) for r in _GENERIC_ROLES if hasattr(controlTypes.Role, r)]
	except Exception:
		return False


def getAdapter(obj, extraApps=()):
	"""Return an adapter for obj, or None when obj is not a terminal.
	extraApps: app names (lower case) whose plain drawing surfaces are treated as terminals."""
	if obj is None:
		return None
	try:
		app = obj.appModule.appName.lower()
	except Exception:
		app = ""
	wcn = getattr(obj, "windowClassName", "") or ""
	try:
		isTerm = isinstance(obj, Terminal) or obj.role == controlTypes.Role.TERMINAL
	except Exception:
		isTerm = False
	if wcn in PUTTY_CLASSES or (app in PUTTY_APPS and isTerm):
		return PuttyAdapter(obj)
	if isTerm:
		try:
			hasUIA = obj.UIATextPattern is not None
		except Exception:
			hasUIA = False
		return UIATerminalAdapter(obj) if hasUIA else BaseAdapter(obj)
	if app in extraApps and _isGenericSurface(obj):
		return DisplayModelAdapter(obj)
	return None


def puttyNonUtf8Sessions():
	"""Saved PuTTY sessions whose character set is set and not UTF-8. Returns None if unreadable."""
	try:
		import winreg
		from urllib.parse import unquote
		res = []
		with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\SimonTatham\PuTTY\Sessions") as root:
			i = 0
			while True:
				try:
					name = winreg.EnumKey(root, i)
				except OSError:
					break
				i += 1
				try:
					with winreg.OpenKey(root, name) as k:
						cp, _ = winreg.QueryValueEx(k, "LineCodePage")
				except OSError:
					continue
				if cp and cp.replace("-", "").lower() != "utf8":
					res.append(unquote(name))
		return res
	except (OSError, ImportError):
		return None
