# TermAssist — show a modal dialog from a script without blocking NVDA.
# Replaces gui.runScriptModalDialog, which NVDA deprecated in 2025.1.
import gui
import wx
from logHandler import log


def run(dialog, callback=None):
	"""Show dialog modally on the GUI thread, then call callback(returnCode) and destroy the dialog."""

	def _show():
		gui.mainFrame.prePopup()
		try:
			res = dialog.ShowModal()
		finally:
			gui.mainFrame.postPopup()
		try:
			if callback:
				callback(res)
		except Exception:
			log.error("TermAssist: dialog callback failed", exc_info=True)
		finally:
			dialog.Destroy()

	wx.CallAfter(_show)
