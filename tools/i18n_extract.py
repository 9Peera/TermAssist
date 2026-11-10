# Extracts tr("english", "thai") pairs from the add-on source.
# Writes: nvda.pot (template for translators) and addon/locale/th/LC_MESSAGES/nvda.po + .mo
# Strings built with f-strings cannot be translated through gettext and are skipped here.
# Run: python tools/i18n_extract.py   (needs: pip install polib)
import ast
import os

import polib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "addon", "globalPlugins", "termAssist")


def pairs():
	seen = {}
	for fn in sorted(os.listdir(SRC)):
		if not fn.endswith(".py"):
			continue
		path = os.path.join(SRC, fn)
		tree = ast.parse(open(path, encoding="utf-8").read())
		for node in ast.walk(tree):
			if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "tr" and len(node.args) == 2:
				a, b = node.args
				if isinstance(a, ast.Constant) and isinstance(b, ast.Constant) and isinstance(a.value, str):
					seen.setdefault(a.value, (b.value, f"globalPlugins/termAssist/{fn}:{node.lineno}"))
	return seen


def meta():
	return {
		"Project-Id-Version": "termAssist",
		"Report-Msgid-Bugs-To": "https://github.com/9Peera/termAssist/issues",
		"MIME-Version": "1.0",
		"Content-Type": "text/plain; charset=UTF-8",
		"Content-Transfer-Encoding": "8bit",
	}


def main():
	p = pairs()
	pot = polib.POFile()
	pot.metadata = meta()
	po = polib.POFile()
	po.metadata = dict(meta(), Language="th")
	for en, (th, occ) in p.items():
		f, line = occ.rsplit(":", 1)
		pot.append(polib.POEntry(msgid=en, msgstr="", occurrences=[(f, line)]))
		po.append(polib.POEntry(msgid=en, msgstr=th, occurrences=[(f, line)]))
	pot.save(os.path.join(ROOT, "nvda.pot"))
	d = os.path.join(ROOT, "addon", "locale", "th", "LC_MESSAGES")
	os.makedirs(d, exist_ok=True)
	po.save(os.path.join(d, "nvda.po"))
	po.save_as_mofile(os.path.join(d, "nvda.mo"))
	print(len(p), "strings")


if __name__ == "__main__":
	main()
