"""Import and exercise the plugin with stubbed NVDA modules (catches typos / wiring errors)."""
import os
import sys
import types
from unittest import mock

ROOT = os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins")
sys.path.insert(0, ROOT)

spoken, beeps, sent = [], [], []


def mod(name, **attrs):
	m = types.ModuleType(name)
	m.__dict__.update(attrs)
	sys.modules[name] = m
	return m


class Conf(dict):
	pass


import ast
import re


class NVDALikeConf:
	"""Mimics NVDA's AggregatedSection: a missing section is cached as KeyError (the 1.0.0 bug)."""

	def __init__(self, data):
		self.spec = {}
		self._data = data
		self._cache = {}

	def __getitem__(self, key):
		if key in self._cache:
			if self._cache[key] is KeyError:
				raise KeyError(key)
			return self._cache[key]
		if key in self._data:
			val = self._data[key]
		elif isinstance(self.spec.get(key), dict):
			val = Conf()
			for k, v in self.spec[key].items():
				m = re.search(r"default=(\"[^\"]*\"|[^,)]+)", v)
				d = m.group(1)
				val[k] = ast.literal_eval(d) if d.startswith('"') else {"True": True, "False": False}.get(d, int(d) if d.isdigit() else d)
		else:
			self._cache[key] = KeyError
			raise KeyError(key)
		self._cache[key] = val
		return val


# nvda.ini without a [termAssist] section, like the user's machine after the update
conf = NVDALikeConf({"keyboard": Conf(speakTypedCharacters=True, speakTypedWords=False)})
mod("config", conf=conf)
config = sys.modules["config"]


def script(**kw):
	def deco(f):
		f.__gestures = kw.get("gesture")
		return f
	return deco


class GP:
	def __init__(self):
		self._g = {}

	def getScript(self, gesture):
		name = self._g.get(gesture.id)
		return getattr(self, "script_" + name) if name else None

	def bindGestures(self, d):
		for k, v in d.items():
			self._g[k] = v

	def clearGestureBindings(self):
		self._g = {}

	def terminate(self):
		pass


mod("globalPluginHandler", GlobalPlugin=GP)
mod("scriptHandler", script=script)
mod("addonHandler", initTranslation=lambda: None)
mod("api", copyToClip=lambda t, notify=False: True, getClipData=lambda: "old", getFocusObject=lambda: None)
mod("core", callLater=lambda ms, f, *a, **k: f(*a, **k))
mod("globalVars", appArgs=types.SimpleNamespace(configPath="/tmp/ta_cfg", secure=False))
modalResults = []
gui = mod("gui", mainFrame=None, messageBox=lambda *a, **k: 2,
	runScriptModalDialog=lambda d, cb: cb(modalResults.pop(0) if isinstance(d, MessageDialog) else 5100))
gui.settingsDialogs = types.SimpleNamespace(NVDASettingsDialog=types.SimpleNamespace(categoryClasses=[]))
mod("gui.guiHelper")
mod("gui.nvdaControls")
mod("gui.settingsDialogs", SettingsPanel=object)
gui.guiHelper = sys.modules["gui.guiHelper"]
gui.nvdaControls = sys.modules["gui.nvdaControls"]
mod("inputCore", decide_executeGesture=mock.MagicMock())
mod("tones", beep=lambda hz, ms: beeps.append(hz))
mod("ui", message=lambda t: spoken.append(t), browseableMessage=lambda t, title=None: spoken.append("VIEW:" + title))


class Timer:
	def Bind(self, *a):
		pass

	def Start(self, *a):
		pass

	def Stop(self):
		pass


answers = []  # scripted dialog answers


class TextEntryDialog:
	def __init__(self, parent, msg, title, value=""):
		self.msg, self.value = msg, value

	def GetValue(self):
		return answers.pop(0)


class SingleChoiceDialog:
	def __init__(self, parent, msg, title, items):
		self.items = items

	def GetSelection(self):
		return self.items.index(answers.pop(0))


class MessageDialog:
	def __init__(self, *a, **k):
		pass

	def SetYesNoCancelLabels(self, *a):
		pass


mod("wx", Timer=Timer, MessageDialog=MessageDialog, CANCEL=0, ICON_QUESTION=0, ID_YES=5103, ID_NO=5104, EVT_TIMER=1, ID_OK=5100, Dialog=object, CallAfter=lambda f, *a, **k: f(*a, **k),
	TextEntryDialog=TextEntryDialog, SingleChoiceDialog=SingleChoiceDialog, YES=2, YES_NO=1, NO_DEFAULT=0, ICON_WARNING=0)


class KIG:
	def __init__(self, key="enter", mods=()):
		self.mainKeyName, self.modifiers = key, set(mods)

	@classmethod
	def fromName(cls, n):
		g = cls(n)
		g.send = lambda: sent.append(("key", n))
		return g


mod("keyboardHandler", KeyboardInputGesture=KIG)
mod("logHandler", log=mock.MagicMock())
mod("languageHandler", getLanguage=lambda: "th")
mod("controlTypes", Role=types.SimpleNamespace(TERMINAL="terminal"))
mod("textInfos", POSITION_ALL=1, POSITION_CARET=2, UNIT_LINE="line")
mod("NVDAObjects")
mod("NVDAObjects.behaviors", Terminal=type("Terminal", (), {}))
import ctypes
ctypes.windll = mock.MagicMock()

import termAssist  # noqa: E402
from termAssist import adapters, modal, sender  # noqa: E402

modal.run = lambda d, cb=None: cb and cb(modalResults.pop(0) if isinstance(d, MessageDialog) else 5100)

sender._paste = lambda text: sent.append(("paste", text))


class FakeAdapter(adapters.BaseAdapter):
	kind, label = "putty", "PuTTY"

	def __init__(self):
		self.hwnd, self.appName, self.screen = 42, "putty", []

	def getLines(self, maxLines=200):
		return self.screen[-maxLines:]

	def getCaretLine(self):
		return self.screen[-1]

	def isAlive(self):
		return True


p = termAssist.GlobalPlugin()
ad = FakeAdapter()
s = termAssist.Session(ad, 5000)
p._sessions[42] = s
p._focusSession = s
c = conf["termAssist"]
assert c["language"] == "auto" and c["pollInterval"] == 400
print("config section ok (registered before first read)")

ad.screen = ["Welcome", "peera@srv:~$ ls -la"]
p._onTimer()
p._decideGesture(gesture=KIG("enter"))
assert s.busy and s.lastCommand == "ls -la"
s.markTime -= 1
ad.screen = ["Welcome", "peera@srv:~$ ls -la", "a.txt", "ls: cannot access x: No such file", "peera@srv:~$"]
p._onTimer()
assert not s.busy, "should be done"
assert s.lastResult == ("ls -la", 2, 1), s.lastResult
assert 880 in beeps and 220 in beeps
print("done/error ok", spoken)

# layer
class G:
	def __init__(self, id, key, isModifier=False):
		self.id, self.mainKeyName, self.isModifier = id, key, isModifier
p.script_layer(None)
assert p._layerActive
fn = p.getScript(G("kb:1", "1"))
fn(G("kb:1", "1"))
assert spoken[-1] == "a.txt" or "cannot" in spoken[-1], spoken[-1]
assert not p._layerActive
print("layer read line 1:", spoken[-1])
p.script_layer(None)
p.getScript(G("kb:x", "x"))(G("kb:x", "x"))
assert not p._layerActive and beeps[-1] == 150
p.script_layer(None)
p.getScript(G("kb:l", "l"))(G("kb:l", "l"))
print("summary:", spoken[-1])
p.script_layer(None)
p.getScript(G("kb:o", "o"))(G("kb:o", "o"))
print(spoken[-1])

# password guard
ad.screen = ["peera@srv:~$ sudo apt update", "[sudo] password for peera:"]
p._onTimer()
assert conf["keyboard"]["speakTypedCharacters"] is False
p._decideGesture(gesture=KIG("enter"))  # enter at password prompt must not re-mark
ad.screen = ["peera@srv:~$ sudo apt update", "[sudo] password for peera:", "Hit:1 http://archive", "Reading"]
p._onTimer()
assert conf["keyboard"]["speakTypedCharacters"] is True
print("password guard ok")

# send with replace line
p._send(s, "df -h", run=True, replaceLine=True, command="df -h")
assert sent[:3] == [("key", "control+e"), ("key", "control+u"), ("paste", "df -h")] and sent[3] == ("key", "enter"), sent
assert s.busy and s.lastCommand == "df -h"
p.script_sessionInfo(None)
print("session:", spoken[-1])

# ---- phase 4: parameter from server list
sent.clear()
s.busy = False
ad.screen = ["peera@srv:~$"]
p._onTimer()
nginx = p.lib.byId["nginx.editsite"]
answers.append("")  # blank -> fetch list
p._fillParams(s, nginx, "insert")
assert p._pending, "fetch should be pending"
fetchCmd = sent[0][1]
token = p._pending["token"]
ad.screen = ["peera@srv:~$ " + fetchCmd, f"__TA_{token}_B__", "default", "shop", f"__TA_{token}_E__", "peera@srv:~$"]
answers.append("shop")
p._onTimer()
assert p._pending is None
assert sent[-1] == ("paste", "sudo nano /etc/nginx/sites-available/shop"), sent[-1]
print("server pick ok:", sent[-1])

# detect services
sent.clear()
ad.screen = ["peera@srv:~$"]
p._onTimer()
p._openLibrary = lambda *a, **k: None
p._detectServices(s, "srv")
token = p._pending["token"]
ad.screen = ["peera@srv:~$ x", f"__TA_{token}_B__", "docker", "nginx", "git", f"__TA_{token}_E__", "peera@srv:~$"]
p._onTimer()
assert p._store.detected("srv") == ["pack.docker", "pack.git", "pack.nginx"], p._store.detected("srv")
print("detect:", spoken[-1])

# high-risk run goes through confirmation, copy action
answers.append("web1")
modalResults.append(5103)  # Yes, run it
p._fillParams(s, p.lib.byId["docker.rm"], "run")
assert sent[-2:] == [("paste", "docker rm web1"), ("key", "enter")], sent[-2:]
n = len(sent)
answers.append("web2")
modalResults.append(5104)  # No: do not run
p._fillParams(s, p.lib.byId["docker.rm"], "run")
assert len(sent) == n, "declined high-risk command must not be sent"
answers.append("web1")
p._fillParams(s, p.lib.byId["docker.logs"], "copy")
assert spoken[-1].endswith("docker logs --tail 100 web1")

# empty value is never sent: re-asked
sent.clear()
answers.extend(["", "1.2.3.4"])
p._fillParams(s, p.lib.byId["x.unban"], "insert")
assert sent == [("paste", "sudo fail2ban-client set sshd unbanip 1.2.3.4")], sent
# fetch refused -> manual entry, still no empty send
sent.clear()
s.busy = True
answers.extend(["", "", "shop"])
p._fillParams(s, p.lib.byId["nginx.editsite"], "insert")
assert sent == [("paste", "sudo nano /etc/nginx/sites-available/shop")], sent
s.busy = False
print("empty-value guard ok")

# pack not installed on this host -> install offered
sent.clear()
p._store.setDetected("srv", ["pack.git"])
modalResults.append(5103)  # Install
p._checkPackInstalled(s, "srv", p.lib.byId["nginx.restart"], "run")
assert sent == [("paste", "sudo apt install -y nginx"), ("key", "enter")], sent
sent.clear()
modalResults.append(5104)  # Use anyway
p._checkPackInstalled(s, "srv", p.lib.byId["nginx.restart"], "insert")
assert sent == [("paste", "sudo systemctl restart nginx")], sent
sent.clear()
p._checkPackInstalled(s, "srv", p.lib.byId["git.status"], "insert")  # installed: no question
assert sent == [("paste", "git status -sb")], sent
print("install warning ok")

# host never checked -> detect automatically, then warn
sent.clear()
s.busy = False
ad.screen = ["root@new1:~#"]
p._onTimer()
modalResults.append(5104)  # Use anyway
p._checkPackInstalled(s, "new1", p.lib.byId["nginx.restart"], "insert")
token = p._pending["token"]
assert "command -v" in sent[0][1]
ad.screen = ["root@new1:~# ...", f"__TA_{token}_B__", "git", f"__TA_{token}_S__0", f"__TA_{token}_E__", "root@new1:~#"]
p._onTimer()
assert p._store.detected("new1") == ["pack.git"]
assert sent[-1] == ("paste", "sudo systemctl restart nginx"), sent
print("auto-detect ok")

# empty list explains why
sent.clear()
s.busy = False
ad.screen = ["root@srv:~#"]
p._onTimer()
answers.extend(["", "x"])
p._fillParams(s, p.lib.byId["nginx.editsite"], "insert")
token = p._pending["token"]
ad.screen = ["root@srv:~# ...", f"__TA_{token}_B__", f"__TA_{token}_S__2", "ls: cannot access '/etc/nginx/sites-available': No such file or directory", f"__TA_{token}_E__", "root@srv:~#"]
p._onTimer()
assert any("ไม่มีโฟลเดอร์หรือไฟล์นี้บนเครื่อง" in m for m in spoken[-3:]), spoken[-3:]
print("empty reason:", [m for m in spoken if "ไม่พบรายการ" in m][-1])

# ---- phase 5: profiles
ad.screen = ["  GNU nano 7.2   /etc/hosts", "127.0.0.1 localhost", "", "", "^G Help  ^O Write Out", "^X Exit  ^R Read File"]
p._onTimer()
assert spoken[-1] == "โปรแกรม nano", spoken[-1]
ad.screen = ["  GNU nano 7.2   /etc/hosts", "127.0.0.1 localhost", "", "[ Wrote 1 line ]", "^G Help  ^O Write Out", "^X Exit  ^R Read File"]
p._onTimer()
assert spoken[-1] == "[ Wrote 1 line ]", spoken[-1]
p.script_profileSummary(None)
print("profile:", spoken[-1])

p.terminate()
print("SMOKE OK")
