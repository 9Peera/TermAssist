# TermAssist — command library and user store (pure Python, no NVDA imports)
# Author: Peera Pilarit
import json
import os
import re
import shlex

PARAM_RE = re.compile(r"\{(\w+)\}")
FAVORITES = "__fav"
RECENT = "__recent"
CUSTOM = "custom"


class Command:
	__slots__ = ("id", "cat", "group", "name", "desc", "keywords", "template", "risk", "sr", "params", "custom", "_hay")

	def __init__(self, d, custom=False):
		self.id = d["id"]
		self.cat = d.get("cat", CUSTOM)
		self.group = d.get("group", "")
		self.name = d.get("name", {})
		if isinstance(self.name, str):
			self.name = {"th": self.name, "en": self.name}
		self.desc = d.get("desc", {}) or {}
		self.keywords = d.get("keywords", [])
		self.template = d["template"]
		self.risk = d.get("risk", "low")
		self.sr = d.get("sr", True)
		self.params = d.get("params", {})
		self.custom = custom
		self._hay = ""

	def label(self, lang):
		return self.name.get(lang) or self.name.get("en") or self.name.get("th") or self.template

	def description(self, lang):
		return self.desc.get(lang) or self.desc.get("en") or ""

	def paramNames(self):
		seen = []
		for p in PARAM_RE.findall(self.template):
			if p not in seen:
				seen.append(p)
		return seen

	def toDict(self):
		return {"id": self.id, "cat": self.cat, "name": self.name, "template": self.template, "risk": self.risk}


class UserStore:
	def __init__(self, path):
		self.path = path
		self.data = {"favorites": [], "recent": [], "custom": [], "detected": {}}
		try:
			with open(path, encoding="utf-8") as f:
				self.data.update(json.load(f))
		except (OSError, ValueError):
			pass

	def save(self):
		try:
			os.makedirs(os.path.dirname(self.path), exist_ok=True)
			with open(self.path, "w", encoding="utf-8") as f:
				json.dump(self.data, f, ensure_ascii=False, indent=1)
		except OSError:
			pass

	def isFavorite(self, cid):
		return cid in self.data["favorites"]

	def toggleFavorite(self, cid):
		fav = self.data["favorites"]
		if cid in fav:
			fav.remove(cid)
			res = False
		else:
			fav.append(cid)
			res = True
		self.save()
		return res

	def addRecent(self, cid, limit=30):
		rec = self.data["recent"]
		if cid in rec:
			rec.remove(cid)
		rec.insert(0, cid)
		del rec[limit:]
		self.save()

	def setDetected(self, host, catIds):
		self.data.setdefault("detected", {})[host or "?"] = list(catIds)
		self.save()

	def detected(self, host):
		return self.data.get("detected", {}).get(host or "?")

	def addCustom(self, name, template):
		n = 1 + max([0] + [int(c["id"].split(".")[-1]) for c in self.data["custom"] if c["id"].split(".")[-1].isdigit()])
		d = {"id": f"custom.{n}", "cat": CUSTOM, "name": {"th": name, "en": name}, "template": template, "risk": "low"}
		self.data["custom"].append(d)
		self.save()
		return d

	def removeCustom(self, cid):
		self.data["custom"] = [c for c in self.data["custom"] if c["id"] != cid]
		for k in ("favorites", "recent"):
			if cid in self.data[k]:
				self.data[k].remove(cid)
		self.save()


class Library:
	def __init__(self, dataFiles, store):
		self.store = store
		self.categories = []  # list of {"id","name":{th,en}}
		self.paramLabels = {}
		self.groups = {}
		self.commands = []
		self.byId = {}
		for path in dataFiles:
			self._loadFile(path)
		self.reloadCustom()

	def _loadFile(self, path):
		try:
			with open(path, encoding="utf-8") as f:
				data = json.load(f)
		except (OSError, ValueError):
			return
		known = {c["id"] for c in self.categories}
		for c in data.get("categories", []):
			if c["id"] not in known:
				self.categories.append(c)
		self.paramLabels.update(data.get("params", {}))
		self.groups.update(data.get("groups", {}))
		for d in data.get("commands", []):
			self._add(Command(d))

	def _add(self, cmd):
		cats = {c["id"]: c for c in self.categories}
		cat = cats.get(cmd.cat, {"name": {}})
		parts = [cmd.template, " ".join(cmd.keywords)] + list(cmd.name.values()) + list(cmd.desc.values()) + list(cat["name"].values())
		cmd._hay = " ".join(parts).lower()
		self.commands.append(cmd)
		self.byId[cmd.id] = cmd

	def reloadCustom(self):
		self.commands = [c for c in self.commands if not c.custom]
		self.byId = {c.id: c for c in self.commands}
		if not any(c["id"] == CUSTOM for c in self.categories):
			self.categories.append({"id": CUSTOM, "name": {"th": "คำสั่งของฉัน", "en": "My commands"}})
		for d in self.store.data.get("custom", []):
			try:
				self._add(Command(d, custom=True))
			except KeyError:
				pass

	def categoryName(self, cid, lang):
		for c in self.categories:
			if c["id"] == cid:
				return c["name"].get(lang) or c["name"].get("en", cid)
		return cid

	def search(self, query="", cat=None):
		if cat == FAVORITES:
			pool = [self.byId[i] for i in self.store.data["favorites"] if i in self.byId]
		elif cat == RECENT:
			pool = [self.byId[i] for i in self.store.data["recent"] if i in self.byId]
		elif cat:
			pool = [c for c in self.commands if c.cat == cat]
		else:
			pool = self.commands
		tokens = query.lower().split()
		if not tokens:
			return list(pool)
		res = []
		for i, c in enumerate(pool):
			if all(t in c._hay for t in tokens):
				names = " ".join(c.name.values()).lower()
				score = 0 if all(t in names for t in tokens) else 1
				if c.template.lower().startswith(tokens[0]):
					score -= 1
				res.append((score, i, c))
		res.sort(key=lambda x: (x[0], x[1]))
		return [c for _, _, c in res]

	def paramLabel(self, name, lang):
		p = self.paramLabels.get(name)
		if not p:
			return name
		return p.get(lang) or p.get("en") or name

	def paramSource(self, name):
		p = self.paramLabels.get(name) or {}
		return p.get("source") or None

	def groupName(self, gid, lang):
		g = self.groups.get(gid)
		if not g:
			return gid
		return g.get(lang) or g.get("en") or gid

	def packs(self):
		return [c for c in self.categories if c.get("detect")]

	def detectCommand(self):
		"""Shell command that prints the detect-binary of every installed pack."""
		bins = sorted({c["detect"] for c in self.packs()})
		return "for c in " + " ".join(bins) + "; do command -v $c >/dev/null 2>&1 && echo $c; done"

	def packOf(self, cmd):
		for c in self.packs():
			if c["id"] == cmd.cat:
				return c
		return None

	def packsForBinaries(self, found):
		found = set(found)
		return [c["id"] for c in self.packs() if c["detect"] in found]

	def orderedCategories(self, detected=None):
		"""Core categories, then installed packs, then the other packs."""
		detected = set(detected or [])
		core = [c for c in self.categories if not c.get("detect") and c["id"] != CUSTOM]
		have = [c for c in self.packs() if c["id"] in detected]
		other = [c for c in self.packs() if c["id"] not in detected]
		mine = [c for c in self.categories if c["id"] == CUSTOM]
		return core + have + other + mine

	def paramDefault(self, name):
		p = self.paramLabels.get(name) or {}
		return p.get("default", "")


def fillTemplate(template, values):
	for k, v in values.items():
		template = template.replace("{" + k + "}", v)
	return template


def buildHeredoc(content, path, sudo=False, append=False, marker="TERMASSIST_EOF"):
	q = shlex.quote(path)
	body = content.replace("\r\n", "\n").rstrip("\n")
	if sudo:
		head = f"sudo tee {'-a ' if append else ''}{q} > /dev/null <<'{marker}'"
	else:
		head = f"cat {'>>' if append else '>'} {q} <<'{marker}'"
	return f"{head}\n{body}\n{marker}"


def buildFetch(command, token, limit=300):
	"""Wrap a command so its output, exit status and first error line can be found between marker lines.
	The quotes split the markers so the typed command line never matches them."""
	m = f"__TA_{token}_"
	return (
		f'__ta_e=$(mktemp); echo {m}""B__; ( {command} ) 2>"$__ta_e" | head -n {limit}; '
		f'echo "{m}""S__${{PIPESTATUS[0]}}"; head -n 1 "$__ta_e"; rm -f "$__ta_e"; unset __ta_e; echo {m}""E__'
	)


def extractFetchInfo(lines, token):
	"""Return {"items": [...], "status": int or None, "error": str} or None if the end marker is not there yet."""
	b, sm, e = f"__TA_{token}_B__", f"__TA_{token}_S__", f"__TA_{token}_E__"
	stripped = [l.strip() for l in lines]
	try:
		start = len(stripped) - 1 - stripped[::-1].index(b)
	except ValueError:
		return None
	rest = stripped[start + 1:]
	if e not in rest:
		return None
	rest = rest[: rest.index(e)]
	status, error = None, ""
	for i, l in enumerate(rest):
		if l.startswith(sm):
			code = l[len(sm):]
			status = int(code) if code.isdigit() else None
			error = " ".join(x for x in rest[i + 1:] if x)
			rest = rest[:i]
			break
	return {"items": [l for l in rest if l], "status": status, "error": error}


def extractFetch(lines, token):
	info = extractFetchInfo(lines, token)
	return None if info is None else info["items"]


def emptyReason(info, th=False):
	"""Explain why a server list came back empty."""
	if not info:
		return "เซิร์ฟเวอร์ไม่ตอบ" if th else "No answer from the server"
	err, status = info.get("error", ""), info.get("status")
	low = err.lower()
	if status == 127 or "command not found" in low or "not found, but can be installed" in low:
		r = ("ไม่พบโปรแกรมที่ใช้ดึงรายการ เครื่องนี้อาจยังไม่ได้ติดตั้ง", "The program is not installed on this server")
	elif any(k in low for k in ("cannot connect", "failed to connect", "daemon is running", "daemon running", "connection refused", "can't connect")):
		r = ("บริการไม่ได้ทำงานอยู่", "The service is not running")
	elif "permission denied" in low or "access denied" in low:
		r = ("ไม่มีสิทธิ์อ่าน ลองใช้ผู้ใช้ที่มีสิทธิ์ sudo", "Permission denied")
	elif "no such file" in low or "cannot access" in low:
		r = ("ไม่มีโฟลเดอร์หรือไฟล์นี้บนเครื่อง", "The folder or file does not exist on this server")
	elif status == 0 and not err:
		r = ("มีอยู่ แต่ยังไม่มีรายการ", "It exists but the list is empty")
	else:
		r = ("คำสั่งดึงรายการล้มเหลว", "The list command failed")
	text = r[0] if th else r[1]
	return f"{text}: {err}" if err else text
