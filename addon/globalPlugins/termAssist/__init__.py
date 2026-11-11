# TermAssist — NVDA add-on for working in PuTTY, KiTTY, Windows Terminal and Windows console
# Copyright (C) 2026 Peera Pilarit
# Released under GPL 2
import functools
import os
import re
import time

import api
import config
import core
import globalPluginHandler
import globalVars
import gui
import inputCore
import tones
import ui
import wx
from keyboardHandler import KeyboardInputGesture
from logHandler import log
from scriptHandler import script

from . import confspec  # noqa: F401  must be first: registers config before anything reads it
from . import adapters, dialogs, library, modal, profiles, prompt, sender, settings, tracker
from .i18n import lang, tr

CATEGORY = "TermAssist"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

LAYER_GESTURES = {f"kb:{d}": "readLine" for d in "123456789"}
LAYER_GESTURES.update({f"kb:shift+{d}": "copyLine" for d in "123456789"})
LAYER_GESTURES.update({
	"kb:c": "commandLibrary",
	"kb:o": "outputViewer",
	"kb:shift+o": "historyViewer",
	"kb:e": "editCommand",
	"kb:m": "compose",
	"kb:r": "readCommand",
	"kb:l": "lastSummary",
	"kb:s": "sessionInfo",
	"kb:t": "readTop",
	"kb:b": "readBottom",
	"kb:a": "toggleDone",
	"kb:d": "diagnostics",
	"kb:p": "profileSummary",
	"kb:h": "layerHelp",
	"kb:escape": "exitLayer",
})

HELP = [
	("1 – 9", "Read the 1st–9th line above the prompt", "อ่านบรรทัดที่ 1–9 นับขึ้นไปจาก prompt"),
	("Shift+1 – 9", "Copy that line", "คัดลอกบรรทัดนั้น"),
	("C", "Command library", "คลังคำสั่ง"),
	("O", "View output of the last command", "ดูผลลัพธ์ของคำสั่งล่าสุด"),
	("Shift+O", "View the whole history", "ดูประวัติทั้งหมด"),
	("E", "Edit the current command line", "แก้ไขคำสั่งในบรรทัดปัจจุบัน"),
	("M", "Compose multi-line text / write a file", "เขียนข้อความหลายบรรทัด / เขียนไฟล์"),
	("R", "Read the current command", "อ่านคำสั่งในบรรทัดปัจจุบัน"),
	("L", "Summary of the last command", "สรุปผลคำสั่งล่าสุด"),
	("S", "Session information", "ข้อมูลเซสชัน"),
	("T / B", "Read the top / bottom line of the screen", "อ่านบรรทัดบนสุด / ล่างสุดของหน้าจอ"),
	("P", "Status of nano / vim / pager / top / htop", "สถานะของ nano / vim / โหมดอ่านทีละหน้า / top / htop"),
	("A", "Toggle the 'command finished' sound", "เปิด/ปิดเสียงแจ้งคำสั่งเสร็จ"),
	("D", "Diagnostics report (copied to clipboard)", "รายงานวินิจฉัย (คัดลอกไปคลิปบอร์ด)"),
	("H", "This help", "ความช่วยเหลือนี้"),
	("Esc", "Leave the layer", "ออกจากโหมดคำสั่ง"),
]


def _finally(func, final):
	@functools.wraps(func)
	def wrapper(gesture):
		try:
			return func(gesture)
		finally:
			final()
	return wrapper


class Session:
	"""State kept for one terminal window."""

	def __init__(self, adapter, historySize):
		self.adapter = adapter
		self.tracker = tracker.OutputTracker(historySize)
		self.busy = False
		self.mark = 0
		self.markTime = 0.0
		self.lastCommand = ""
		self.errorNotified = False
		self.lastResult = None  # (command, lineCount, errorCount)
		self.profile = None
		self.profState = {}

	def markCommand(self, command):
		self.busy = True
		self.mark = self.tracker.total
		self.markTime = time.monotonic()
		self.lastCommand = command
		self.errorNotified = False


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = CATEGORY

	def __init__(self):
		super().__init__()
		settings.init()
		self._sessions = {}
		self._focusSession = None
		self._layerActive = False
		self._pwSaved = None
		self._detector = prompt.PromptDetector(settings.conf()["promptRegex"])
		self._store = library.UserStore(os.path.join(globalVars.appArgs.configPath, "termAssist.json"))
		self._lib = None
		self._pending = None  # running server lookup
		self._fetchSeq = 0
		self._lastFetch = None
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(settings.TermAssistPanel)
		try:
			inputCore.decide_executeGesture.register(self._decideGesture)
		except AttributeError:
			log.warning("TermAssist: decide_executeGesture not available; command tracking disabled")
		self._timer = wx.Timer()
		self._timer.Bind(wx.EVT_TIMER, self._onTimer)
		self._timer.Start(settings.conf()["pollInterval"])
		self._interval = settings.conf()["pollInterval"]

	def terminate(self):
		try:
			self._timer.Stop()
		except Exception:
			pass
		self._restorePasswordGuard()
		try:
			inputCore.decide_executeGesture.unregister(self._decideGesture)
		except Exception:
			pass
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(settings.TermAssistPanel)
		except ValueError:
			pass
		super().terminate()

	# ------------------------------------------------------------ helpers
	@property
	def lib(self):
		if self._lib is None:
			files = []
			for d, _dirs, names in sorted(os.walk(DATA_DIR)):
				files += [os.path.join(d, f) for f in sorted(names) if f.endswith(".json")]
			self._lib = library.Library(files, self._store)
		return self._lib

	def _getDetector(self):
		pat = settings.conf()["promptRegex"]
		if (pat or prompt.DEFAULT_PROMPT) != self._detector.pattern:
			self._detector = prompt.PromptDetector(pat)
		return self._detector

	def _session(self):
		s = self._focusSession
		if not s:
			ui.message(tr("Not in a terminal", "ไม่ได้อยู่ในเทอร์มินัล"))
		return s

	def _screenLines(self, s):
		try:
			return s.adapter.getLines(300)
		except Exception:
			log.debugWarning("TermAssist: getLines failed", exc_info=True)
			return []

	def _linesAbovePrompt(self, s):
		lines = self._screenLines(s)
		if lines and self._getDetector().match(lines[-1]):
			lines = lines[:-1]
		return lines

	def _lastOutput(self, s):
		lines = s.tracker.since(s.mark)
		if lines and self._getDetector().match(lines[0]):
			lines = lines[1:]
		return lines

	def _send(self, s, text, run=False, replaceLine=False, command=None):
		c = settings.conf()
		clear = [k for k in c["clearLineKeys"].split(",") if k.strip()] if replaceLine else None

		def onEnter():
			s.markCommand(command if command is not None else text.split("\n")[0])

		core.callLater(
			300, sender.send, s.adapter, text,
			enter=run, clearKeys=clear, method=c["sendMethod"], onEnter=onEnter if run else None,
		)

	# ------------------------------------------------------------ focus and tracking
	def event_gainFocus(self, obj, nextHandler):
		try:
			ad = adapters.getAdapter(obj, settings.extraApps())
		except Exception:
			log.debugWarning("TermAssist: getAdapter failed", exc_info=True)
			ad = None
		if ad and ad.hwnd:
			s = self._sessions.get(ad.hwnd)
			if s:
				s.adapter = ad
			else:
				s = self._sessions[ad.hwnd] = Session(ad, settings.conf()["historySize"])
			self._focusSession = s
		else:
			self._focusSession = None
			self._restorePasswordGuard()
		nextHandler()

	def _decideGesture(self, gesture=None, **kwargs):
		try:
			s = self._focusSession
			if (
				s and not self._layerActive and isinstance(gesture, KeyboardInputGesture)
				and gesture.mainKeyName in ("enter", "numpadEnter") and not gesture.modifiers
			):
				# Only an Enter typed at a shell prompt starts a new command.
				# Enter at a password prompt, inside nano, or answering y/n keeps the current one.
				p, cmd = self._getDetector().split(s.adapter.getCaretLine())
				if p is not None and self._pwSaved is None:
					s.markCommand(cmd)
		except Exception:
			log.debugWarning("TermAssist: decideGesture failed", exc_info=True)
		return True

	def _onTimer(self, evt=None):
		c = settings.conf()
		if c["pollInterval"] != self._interval:
			self._interval = c["pollInterval"]
			self._timer.Start(self._interval)
		targets = []
		if self._focusSession:
			targets.append(self._focusSession)
		targets += [s for s in self._sessions.values() if s.busy and s is not self._focusSession]
		if self._pending and self._pending["session"] not in targets:
			targets.append(self._pending["session"])
		for s in targets:
			try:
				self._poll(s, s is self._focusSession, c)
			except Exception:
				log.debugWarning("TermAssist: poll failed", exc_info=True)
				if not s.adapter.isAlive():
					self._sessions.pop(s.adapter.hwnd, None)
		self._checkFetch()
		# forget closed windows
		for hwnd in [h for h, s in self._sessions.items() if s is not self._focusSession and not s.busy]:
			if not self._sessions[hwnd].adapter.isAlive():
				del self._sessions[hwnd]

	def _poll(self, s, focused, c):
		lines = s.adapter.getLines(300)
		s.tracker.resize(c["historySize"])
		new = s.tracker.update(lines)
		last = lines[-1] if lines else ""
		det = self._getDetector()
		if s.busy and new and c["errorSound"] and not s.errorNotified and prompt.hasError(new):
			s.errorNotified = True
			tones.beep(220, 120)
		if focused:
			self._checkPassword(last, c)
			self._checkProfile(s, lines, c)
		if s.busy and det.isIdlePrompt(last) and time.monotonic() - s.markTime > 0.25:
			self._onDone(s, focused, c)

	def _onDone(self, s, focused, c):
		s.busy = False
		out = self._lastOutput(s)
		errors = prompt.countErrors(out)
		s.lastResult = (s.lastCommand, len(out), errors)
		if c["announceDone"]:
			tones.beep(880, 50)
		if not focused and c["notifyBackground"]:
			ui.message(tr(f"Finished in {s.adapter.label}: {s.lastCommand}", f"คำสั่งเสร็จใน {s.adapter.label}: {s.lastCommand}"))
		elif focused and c["speakLineCount"] and out:
			ui.message(tr(f"{len(out)} lines", f"{len(out)} บรรทัด"))

	# ------------------------------------------------------------ full-screen profiles
	def _checkProfile(self, s, lines, c):
		prof = profiles.detect(lines)
		st = profiles.state(prof, lines)
		th = lang() == "th"
		if prof != s.profile:
			if c["profileAnnounce"]:
				if prof:
					ui.message(profiles.NAMES[prof][1 if th else 0])
				elif s.profile:
					tones.beep(400, 30)
			s.profile, s.profState = prof, st
			return
		if prof and c["profileAnnounce"]:
			for msg in profiles.events(prof, s.profState, st):
				if msg == "END":
					msg = tr("End", "จบเอกสาร")
				ui.message(msg)
		s.profState = st

	@script(description=tr("TermAssist: status of nano, vim, pager, top or htop", "TermAssist: สถานะของ nano, vim, โหมดอ่านทีละหน้า, top หรือ htop"))
	def script_profileSummary(self, gesture):
		s = self._session()
		if not s:
			return
		lines = self._screenLines(s)
		prof = profiles.detect(lines)
		if not prof:
			ui.message(tr("No full-screen program detected", "ไม่พบโปรแกรมเต็มจอ"))
			return
		th = lang() == "th"
		ui.message(profiles.NAMES[prof][1 if th else 0] + ". " + profiles.summary(prof, profiles.state(prof, lines), th))

	# ------------------------------------------------------------ server lookups
	def _fetch(self, s, command, callback):
		"""Run command in the terminal and call callback(list of lines) — or callback(None) on failure."""
		last = (self._screenLines(s) or [""])[-1]
		idle = self._getDetector().isIdlePrompt(last) or bool(re.search(r"[$#>%]\s*$", last))
		if s.busy or s.profile or not idle:
			why = "busy" if s.busy else ("full-screen " + s.profile if s.profile else "no prompt")
			self._lastFetch = {"command": command, "result": f"refused ({why})", "lastLine": last}
			ui.message(tr("The terminal is not at a prompt; type the value instead", "เทอร์มินัลยังไม่อยู่ที่ prompt กรุณาพิมพ์ค่าเอง"))
			wx.CallAfter(callback, None, None)
			return
		self._fetchSeq += 1
		token = f"{int(time.time()) % 100000}{self._fetchSeq}"
		self._pending = {"session": s, "token": token, "cb": callback, "deadline": time.monotonic() + 20, "mark": s.tracker.total}
		self._lastFetch = {"command": command, "token": token, "result": "pending", "lastLine": last}
		ui.message(tr("Getting the list from the server", "กำลังดึงรายการจากเซิร์ฟเวอร์"))
		core.callLater(300, sender.send, s.adapter, library.buildFetch(command, token), enter=True, method=settings.conf()["sendMethod"])

	def _checkFetch(self):
		p = self._pending
		if not p:
			return
		s = p["session"]
		screen = self._screenLines(s)
		info = library.extractFetchInfo(s.tracker.since(p["mark"]) + screen, p["token"])
		if info is not None:
			self._pending = None
			self._lastFetch["result"] = f"ok, {len(info['items'])} items, status {info['status']}"
			if info["error"]:
				self._lastFetch["error"] = info["error"]
			wx.CallAfter(p["cb"], info["items"], info)
			return
		if self._pwSaved is not None:
			p["deadline"] += self._interval / 1000.0  # waiting for a sudo password
		if time.monotonic() > p["deadline"]:
			self._pending = None
			self._lastFetch["result"] = "timeout"
			self._lastFetch["screen"] = screen[-8:]
			ui.message(tr("No answer from the server", "เซิร์ฟเวอร์ไม่ตอบ"))
			wx.CallAfter(p["cb"], None, None)

	# ------------------------------------------------------------ password guard
	def _checkPassword(self, last, c):
		isPw = c["passwordGuard"] and prompt.isPasswordPrompt(last)
		if isPw and self._pwSaved is None:
			kb = config.conf["keyboard"]
			self._pwSaved = (kb["speakTypedCharacters"], kb["speakTypedWords"])
			kb["speakTypedCharacters"] = False
			kb["speakTypedWords"] = False
			tones.beep(660, 50)
			core.callLater(90, tones.beep, 990, 50)
			ui.message(tr("Password prompt, typing echo muted", "ป้อนรหัสผ่าน ปิดเสียงตัวอักษรที่พิมพ์แล้ว"))
		elif not isPw and self._pwSaved is not None:
			self._restorePasswordGuard()

	def _restorePasswordGuard(self):
		if self._pwSaved is None:
			return
		kb = config.conf["keyboard"]
		kb["speakTypedCharacters"], kb["speakTypedWords"] = self._pwSaved
		self._pwSaved = None

	# ------------------------------------------------------------ layer
	def getScript(self, gesture):
		if not self._layerActive:
			return super().getScript(gesture)
		if getattr(gesture, "isModifier", False):
			return None
		s = super().getScript(gesture) or self.script_layerUnknown
		return _finally(s, self._exitLayer)

	def _exitLayer(self):
		if self._layerActive:
			self._layerActive = False
			self.clearGestureBindings()
			# class-level gestures collected by NVDA's ScriptableType from @script(gesture=...)
			self.bindGestures(getattr(self, "_GlobalPlugin__gestures", {"kb:NVDA+control+shift+p": "layer"}))

	@script(
		description=tr("Enter the TermAssist command layer", "เข้าโหมดคำสั่ง TermAssist"),
		gesture="kb:NVDA+control+shift+p",
	)
	def script_layer(self, gesture):
		if not self._session():
			return
		self._layerActive = True
		self.bindGestures(LAYER_GESTURES)
		tones.beep(500, 40)

	def script_layerUnknown(self, gesture):
		tones.beep(150, 80)

	def script_exitLayer(self, gesture):
		tones.beep(300, 40)

	@script(description=tr("TermAssist: list layer commands", "TermAssist: แสดงปุ่มในโหมดคำสั่ง"))
	def script_layerHelp(self, gesture):
		th = lang() == "th"
		rows = "\n".join(f"{k}: {t if th else e}" for k, e, t in HELP)
		head = tr("Press NVDA+Control+Shift+P, then:", "กด NVDA+Control+Shift+P แล้วกด:")
		ui.browseableMessage(f"{head}\n\n{rows}", tr("TermAssist help", "ความช่วยเหลือ TermAssist"))

	# ------------------------------------------------------------ reading
	def script_readLine(self, gesture):
		s = self._session()
		if not s:
			return
		n = int(gesture.mainKeyName)
		lines = self._linesAbovePrompt(s)
		if n > len(lines):
			ui.message(tr("No line", "ไม่มีบรรทัด"))
			return
		text = lines[-n]
		ui.message(text if text.strip() else tr("blank", "ว่าง"))

	def script_copyLine(self, gesture):
		s = self._session()
		if not s:
			return
		n = int(gesture.mainKeyName)
		lines = self._linesAbovePrompt(s)
		if n > len(lines) or not lines[-n].strip():
			ui.message(tr("Nothing to copy", "ไม่มีข้อความให้คัดลอก"))
			return
		api.copyToClip(lines[-n], notify=False)
		ui.message(tr("Copied: ", "คัดลอกแล้ว: ") + lines[-n])

	@script(description=tr("TermAssist: read the current command", "TermAssist: อ่านคำสั่งในบรรทัดปัจจุบัน"))
	def script_readCommand(self, gesture):
		s = self._session()
		if not s:
			return
		_p, cmd = self._getDetector().split(s.adapter.getCaretLine())
		ui.message(cmd if cmd else tr("Command line is empty", "บรรทัดคำสั่งว่าง"))

	@script(description=tr("TermAssist: read the top line of the screen", "TermAssist: อ่านบรรทัดบนสุดของหน้าจอ"))
	def script_readTop(self, gesture):
		s = self._session()
		if s:
			lines = [l for l in self._screenLines(s)[-60:] if l.strip()]
			ui.message(lines[0] if lines else tr("blank", "ว่าง"))

	@script(description=tr("TermAssist: read the bottom line of the screen", "TermAssist: อ่านบรรทัดล่างสุดของหน้าจอ"))
	def script_readBottom(self, gesture):
		s = self._session()
		if s:
			lines = self._screenLines(s)
			ui.message(lines[-1] if lines else tr("blank", "ว่าง"))

	@script(description=tr("TermAssist: summary of the last command", "TermAssist: สรุปผลคำสั่งล่าสุด"))
	def script_lastSummary(self, gesture):
		s = self._session()
		if not s:
			return
		if s.busy:
			n = len(self._lastOutput(s))
			ui.message(tr(f"Still running: {s.lastCommand}, {n} lines so far", f"ยังทำงานอยู่: {s.lastCommand} ได้ {n} บรรทัดแล้ว"))
			return
		if not s.lastResult:
			ui.message(tr("No command yet", "ยังไม่มีคำสั่ง"))
			return
		cmd, n, err = s.lastResult
		msg = tr(f"{cmd}: {n} lines", f"{cmd}: {n} บรรทัด")
		if err:
			msg += tr(f", {err} lines look like errors", f", มี {err} บรรทัดที่น่าจะเป็นข้อผิดพลาด")
		ui.message(msg)

	@script(description=tr("TermAssist: view output of the last command", "TermAssist: ดูผลลัพธ์ของคำสั่งล่าสุด"))
	def script_outputViewer(self, gesture):
		s = self._session()
		if not s:
			return
		out = self._lastOutput(s)
		if not out:
			ui.message(tr("No output", "ไม่มีผลลัพธ์"))
			return
		title = tr("Output: ", "ผลลัพธ์: ") + (s.lastCommand or "")
		ui.browseableMessage("\n".join(out), title)

	@script(description=tr("TermAssist: view the whole output history", "TermAssist: ดูประวัติผลลัพธ์ทั้งหมด"))
	def script_historyViewer(self, gesture):
		s = self._session()
		if not s:
			return
		lines = s.tracker.all() + self._screenLines(s)[-1:]
		if not lines:
			ui.message(tr("No history", "ไม่มีประวัติ"))
			return
		ui.browseableMessage("\n".join(lines), tr("Terminal history", "ประวัติเทอร์มินัล"))

	@script(description=tr("TermAssist: session information", "TermAssist: ข้อมูลเซสชัน"))
	def script_sessionInfo(self, gesture):
		s = self._session()
		if not s:
			return
		parts = []
		p, _cmd = self._getDetector().split(s.adapter.getCaretLine())
		info = prompt.parseSession(p or "")
		if info:
			u, h, path = info
			parts.append(tr(f"User {u}, host {h}", f"ผู้ใช้ {u} เครื่อง {h}") + (tr(f", folder {path}", f" โฟลเดอร์ {path}") if path else ""))
		else:
			parts.append(tr("Prompt not recognized", "ไม่รู้จักรูปแบบ prompt"))
		parts.append(s.adapter.label)
		if s.busy:
			parts.append(tr("command running", "คำสั่งกำลังทำงาน"))
		if s.adapter.kind == "putty":
			bad = adapters.puttyNonUtf8Sessions()
			if bad:
				parts.append(tr(
					f"Warning: saved sessions not using UTF-8: {', '.join(bad)}",
					f"คำเตือน: เซสชันที่ยังไม่ได้ตั้งเป็น UTF-8: {', '.join(bad)}",
				))
		ui.message(". ".join(parts))

	@script(description=tr("TermAssist: toggle the command finished sound", "TermAssist: เปิด/ปิดเสียงแจ้งคำสั่งเสร็จ"))
	def script_toggleDone(self, gesture):
		c = settings.conf()
		c["announceDone"] = not c["announceDone"]
		ui.message(tr("Finished sound on", "เปิดเสียงแจ้งคำสั่งเสร็จ") if c["announceDone"] else tr("Finished sound off", "ปิดเสียงแจ้งคำสั่งเสร็จ"))

	@script(description=tr("TermAssist: diagnostics report", "TermAssist: รายงานวินิจฉัย"))
	def script_diagnostics(self, gesture):
		obj = api.getFocusObject()
		try:
			import buildVersion as bv
		except ImportError:
			import versionInfo as bv
		s = self._focusSession
		rep = [
			"TermAssist diagnostics",
			f"NVDA: {getattr(bv, 'version', '?')}",
			f"App: {getattr(obj.appModule, 'appName', '?')}",
			f"Window class: {getattr(obj, 'windowClassName', '?')}",
			f"Role: {obj.role}",
			"Classes: " + ", ".join(c.__name__ for c in type(obj).__mro__[:8]),
		]
		if s:
			t0 = time.perf_counter()
			lines = self._screenLines(s)
			ms = (time.perf_counter() - t0) * 1000
			caret = s.adapter.getCaretLine()
			p, cmd = self._getDetector().split(caret)
			rep += [
				f"Adapter: {s.adapter.kind} ({s.adapter.label})",
				f"Lines read: {len(lines)} in {ms:.1f} ms",
				f"History lines: {s.tracker.total}, full-screen mode: {s.tracker.inFullScreenMode}",
				f"Caret line: {caret!r}",
				f"Prompt: {p!r}  Command: {cmd!r}",
				f"Busy: {s.busy}  Last command: {s.lastCommand!r}",
				f"Send method: {settings.conf()['sendMethod']}",
				"Last 5 lines:",
			] + [f"  {l!r}" for l in lines[-5:]]
		else:
			rep.append("Adapter: none (focus is not a recognized terminal)")
		if s:
			host = self._host(s)
			det = self._store.detected(host)
			rep.append(f"Host: {host!r}  Detected services: {det if det is not None else 'not checked yet'}")
		if self._lastFetch:
			rep.append("Last server lookup:")
			rep += [f"  {k}: {v!r}" for k, v in self._lastFetch.items()]
		text = "\n".join(rep)
		api.copyToClip(text, notify=False)
		ui.browseableMessage(text, tr("TermAssist diagnostics (copied)", "รายงานวินิจฉัย TermAssist (คัดลอกแล้ว)"))

	# ------------------------------------------------------------ input and editing
	@script(description=tr("TermAssist: edit the current command line", "TermAssist: แก้ไขคำสั่งในบรรทัดปัจจุบัน"))
	def script_editCommand(self, gesture):
		s = self._session()
		if not s:
			return
		_p, cmd = self._getDetector().split(s.adapter.getCaretLine())
		dlg = dialogs.EditCommandDialog(gui.mainFrame, cmd)

		def done(res):
			if res == wx.ID_OK and dlg.action:
				self._send(s, dlg.value, run=dlg.action == "run", replaceLine=True, command=dlg.value)

		modal.run(dlg, done)

	@script(description=tr("TermAssist: compose multi-line text or write a file", "TermAssist: เขียนข้อความหลายบรรทัดหรือเขียนไฟล์"))
	def script_compose(self, gesture):
		s = self._session()
		if not s:
			return
		dlg = dialogs.ComposeDialog(gui.mainFrame)

		def done(res):
			if res == wx.ID_OK and dlg.result:
				text, enter = dlg.result
				self._send(s, text, run=enter, command=text.split("\n")[0])

		modal.run(dlg, done)

	@script(description=tr("TermAssist: command library", "TermAssist: คลังคำสั่ง"))
	def script_commandLibrary(self, gesture):
		s = self._session()
		if s:
			self._openLibrary(s)

	def _host(self, s):
		p, _cmd = self._getDetector().split(s.adapter.getCaretLine())
		info = prompt.parseSession(p or "")
		return info[1] if info else None

	def _openLibrary(self, s, catId=None):
		host = self._host(s)
		dlg = dialogs.PaletteDialog(gui.mainFrame, self.lib, self._store, host=host, catId=catId)

		def done(res):
			if res != wx.ID_OK or not dlg.result:
				return
			cmd, action = dlg.result
			if action == "detect":
				core.callLater(300, self._detectServices, s, host)
			else:
				wx.CallAfter(self._checkPackInstalled, s, host, cmd, action)

		modal.run(dlg, done)

	def _checkPackInstalled(self, s, host, cmd, action):
		"""Warn when a service pack command is used on a host where the service was not detected."""
		pack = self.lib.packOf(cmd)
		detected = self._store.detected(host)
		needsCheck = pack and cmd.group != "check" and action != "copy"
		if needsCheck and detected is None:
			# First service command on this host: detect installed services once, then decide.
			def got(items, info=None):
				if items is None:
					self._fillParams(s, cmd, action)
					return
				self._store.setDetected(host, self.lib.packsForBinaries(items))
				self._checkPackInstalled(s, host, cmd, action)

			ui.message(tr("Checking which services this server has", "กำลังตรวจว่าเครื่องนี้มีบริการอะไรบ้าง"))
			core.callLater(300, self._fetch, s, self.lib.detectCommand(), got)
			return
		if not needsCheck or pack["id"] in detected:
			self._fillParams(s, cmd, action)
			return
		L = lang()
		name = self.lib.categoryName(pack["id"], L)
		install = f"sudo apt install -y {pack['install']}"
		msg = tr(
			f"{name} was not found on {host} at the last check.\n\nInstall it now with:\n{install}\n\nYes: install. No: use the command anyway. Cancel: stop.",
			f"ตรวจครั้งล่าสุดไม่พบ {name} บนเครื่อง {host}\n\nติดตั้งตอนนี้ด้วยคำสั่ง:\n{install}\n\nใช่: ติดตั้ง  ไม่: ใช้คำสั่งต่อ  ยกเลิก: หยุด",
		)
		dlg = wx.MessageDialog(gui.mainFrame, msg, tr("Service not installed", "ยังไม่ได้ติดตั้งบริการ"), wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
		try:
			dlg.SetYesNoCancelLabels(tr("&Install", "&ติดตั้ง"), tr("&Use anyway", "&ใช้คำสั่งต่อ"), tr("Cancel", "ยกเลิก"))
		except Exception:
			pass

		def done(res):
			if res == wx.ID_YES:
				ui.message(tr("Installing. Run Detect services again when it finishes.", "กำลังติดตั้ง เมื่อเสร็จแล้วให้กดตรวจหาบริการในเครื่องอีกครั้ง"))
				self._send(s, install, run=True, command=install)
			elif res == wx.ID_NO:
				wx.CallAfter(self._fillParams, s, cmd, action)

		modal.run(dlg, done)

	def _detectServices(self, s, host):
		def got(items, info=None):
			if items is None:
				return
			ids = self.lib.packsForBinaries(items)
			self._store.setDetected(host, ids)
			names = ", ".join(self.lib.categoryName(i, lang()) for i in ids) or tr("none", "ไม่มี")
			ui.message(tr(f"Found {len(ids)} services: {names}", f"พบ {len(ids)} บริการ: {names}"))
			core.callLater(800, self._openLibrary, s, ids[0] if ids else None)

		self._fetch(s, self.lib.detectCommand(), got)

	def _fillParams(self, s, cmd, action):
		"""Ask each {parameter}. A blank answer for a parameter with a server source fetches a list."""
		L = lang()
		names = cmd.paramNames()
		values = {}
		title = cmd.label(L)

		def ask(i, allowFetch=True):
			if i >= len(names):
				finish()
				return
			p = names[i]
			src = self.lib.paramSource(p) if allowFetch else None
			msg = self.lib.paramLabel(p, L) + ":"
			if src:
				msg += "\n" + tr("(Leave blank and press OK to choose from a list on the server)", "(เว้นว่างแล้วกด ตกลง เพื่อเลือกจากรายการบนเซิร์ฟเวอร์)")
			elif self.lib.paramSource(p):
				msg += "\n" + tr("(Type the value. Press Cancel to stop.)", "(พิมพ์ค่าเอง หรือกด ยกเลิก เพื่อหยุด)")
			dlg = wx.TextEntryDialog(gui.mainFrame, msg, title, value=self.lib.paramDefault(p))

			def done(res):
				if res != wx.ID_OK:
					return
				v = dlg.GetValue().strip()
				if not v and src:
					core.callLater(300, self._fetch, s, src, lambda items, info: pick(i, items, info))
					return
				if not v:
					ui.message(tr("A value is required; command not sent", "ต้องกรอกค่า จึงยังไม่ส่งคำสั่ง"))
					wx.CallAfter(ask, i, False)
					return
				values[p] = v
				wx.CallAfter(ask, i + 1)

			modal.run(dlg, done)

		def pick(i, items, info=None):
			if not items:
				if items is not None:
					ui.message(tr("No items. ", "ไม่พบรายการ ") + library.emptyReason(info, lang() == "th"))
				ask(i, allowFetch=False)
				return
			p = names[i]
			dlg = wx.SingleChoiceDialog(gui.mainFrame, self.lib.paramLabel(p, L) + ":", title, items)

			def done(res):
				if res != wx.ID_OK:
					return
				values[p] = items[dlg.GetSelection()]
				wx.CallAfter(ask, i + 1)

			modal.run(dlg, done)

		def finish():
			text = library.fillTemplate(cmd.template, values)
			self._store.addRecent(cmd.id)
			if action == "copy":
				api.copyToClip(text, notify=False)
				ui.message(tr("Copied: ", "คัดลอกแล้ว: ") + text)
				return
			if action == "run" and cmd.risk == "high":
				msg = tr(f"This command is high risk:\n{text}\n\nRun it now?", f"คำสั่งนี้มีความเสี่ยงสูง:\n{text}\n\nต้องการรันทันทีหรือไม่")
				dlg = wx.MessageDialog(gui.mainFrame, msg, tr("Confirm", "ยืนยัน"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
				modal.run(dlg, lambda res: res == wx.ID_YES and self._send(s, text, run=True, command=text))
				return
			self._send(s, text, run=action == "run", command=text)

		ask(0)


if globalVars.appArgs.secure:
	GlobalPlugin = globalPluginHandler.GlobalPlugin  # noqa: F811
