# TermAssist — sending text and keys into the terminal
# Author: Peera Pilarit
import ctypes
from ctypes import wintypes

import api
import core
from keyboardHandler import KeyboardInputGesture
from logHandler import log

WM_CHAR = 0x0102
_PostMessageW = ctypes.windll.user32.PostMessageW
_PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_PostMessageW.restype = wintypes.BOOL

PASTE_KEY = "shift+insert"  # works in PuTTY, KiTTY, Windows Terminal and conhost


def pressKeys(names):
	for n in names:
		n = n.strip()
		if n:
			try:
				KeyboardInputGesture.fromName(n).send()
			except Exception:
				log.error(f"TermAssist: cannot send key {n!r}", exc_info=True)


def _restoreClip(old):
	try:
		api.copyToClip(old, notify=False)
	except Exception:
		pass


def _paste(text):
	try:
		old = api.getClipData()
	except Exception:
		old = None
	api.copyToClip(text.replace("\r\n", "\n").replace("\n", "\r\n"), notify=False)
	pressKeys([PASTE_KEY])
	if old is not None:
		core.callLater(1200, _restoreClip, old)


def _type(hwnd, text):
	for ch in text.replace("\r\n", "\n"):
		_PostMessageW(hwnd, WM_CHAR, 13 if ch == "\n" else ord(ch), 0)


def send(adapter, text, enter=False, clearKeys=None, method="paste", onEnter=None):
	"""Send text to the terminal. Steps are spaced so the terminal can keep up."""
	useType = method == "type" and adapter.supportsTypeMethod and adapter.hwnd

	def step2():
		if text:
			if useType:
				_type(adapter.hwnd, text)
			else:
				_paste(text)
		if enter:
			core.callLater(200, step3)

	def step3():
		if useType:
			_type(adapter.hwnd, "\n")
		else:
			pressKeys(["enter"])
		if onEnter:
			onEnter()

	if clearKeys:
		pressKeys(clearKeys)
		core.callLater(80, step2)
	else:
		step2()
