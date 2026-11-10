# TermAssist — full-screen program profiles: nano, vim, less/man, top, htop (pure Python)
# Author: Peera Pilarit
import re

VIM_MODE = re.compile(r"^-- (INSERT|VISUAL BLOCK|VISUAL LINE|VISUAL|REPLACE)(?: --)?")
VIM_RULER = re.compile(r"(\d+),(\d+)(?:-\d+)?\s+(All|Top|Bot|\d+%)\s*$")
LESS_BOTTOM = re.compile(r"^(?::|\(END\)|lines \d+-\d+.*|.*press h for help or q to quit.*|.*\(END\).*|.*\d+%\s*)$")
NANO_SHORTCUT = re.compile(r"\^[A-Z_\\]\s")

NAMES = {
	"nano": ("nano editor", "โปรแกรม nano"),
	"vim": ("vim editor", "โปรแกรม vim"),
	"less": ("pager", "โหมดอ่านทีละหน้า"),
	"top": ("top", "top"),
	"htop": ("htop", "htop"),
}


def detect(lines):
	if len(lines) < 3:
		return None
	top, bottom = lines[0], lines[-1]
	if "GNU nano" in top or (NANO_SHORTCUT.search(lines[-1]) and NANO_SHORTCUT.search(lines[-2]) and "^X" in lines[-1] + lines[-2]):
		return "nano"
	if top.lstrip().startswith("top - "):
		return "top"
	head = lines[:8]
	if any("Load average:" in l for l in head) and any("Tasks:" in l for l in head):
		return "htop"
	tildes = sum(1 for l in lines if l.strip() == "~")
	if VIM_MODE.match(bottom) or (VIM_RULER.search(bottom) and tildes >= 1) or tildes >= 3:
		return "vim"
	if LESS_BOTTOM.match(bottom.strip()) and (bottom.strip() in (":", "(END)") or "(END)" in bottom or "lines " in bottom or "press h" in bottom):
		return "less"
	return None


def state(profile, lines):
	"""Small dict describing what matters on screen for this profile."""
	if not profile or not lines:
		return {}
	bottom = lines[-1].strip()
	if profile == "nano":
		title = re.sub(r"^\s*GNU nano [\d.]+\s*", "", lines[0]).strip()
		status = lines[-3].strip() if len(lines) >= 3 else ""
		if NANO_SHORTCUT.search(status):
			status = ""
		return {"title": title, "status": status}
	if profile == "vim":
		m = VIM_MODE.match(bottom)
		mode = m.group(1) if m else ("COMMAND" if bottom[:1] in (":", "/", "?") else "NORMAL")
		r = VIM_RULER.search(bottom)
		pos = f"{r.group(1)},{r.group(2)} {r.group(3)}" if r else ""
		return {"mode": mode, "pos": pos, "status": bottom}
	if profile == "less":
		return {"status": bottom, "end": "(END)" in bottom}
	if profile == "top":
		return {"summary": [l.strip() for l in lines[:5] if l.strip()]}
	if profile == "htop":
		keys = ("Tasks:", "Load average:", "Uptime:", "Mem", "Swp")
		return {"summary": [l.strip() for l in lines[:10] if any(k in l for k in keys)]}
	return {}


def events(profile, old, new):
	"""Messages worth speaking when the profile state changes."""
	out = []
	if profile == "nano":
		if new.get("status") and new["status"] != old.get("status"):
			out.append(new["status"])
	elif profile == "vim":
		if new.get("mode") != old.get("mode") and new.get("mode") != "COMMAND":
			out.append(new["mode"])
	elif profile == "less":
		if new.get("end") and not old.get("end"):
			out.append("END")
	return out


def summary(profile, st, th=False):
	if profile == "nano":
		t = st.get("title") or ("ไฟล์ใหม่" if th else "new file")
		return t + (". " + st["status"] if st.get("status") else "")
	if profile == "vim":
		return " ".join(x for x in (st.get("mode"), st.get("pos")) if x)
	if profile == "less":
		return st.get("status", "")
	if profile in ("top", "htop"):
		return ". ".join(st.get("summary", []))
	return ""
