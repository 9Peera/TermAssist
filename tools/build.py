# Build termAssist-<version>.nvda-addon
# Run: python tools/build.py
import configparser
import os
import zipfile

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(ROOT, "addon")


def html(md_path, out_path, lang):
	with open(md_path, encoding="utf-8") as f:
		body = markdown.markdown(f.read(), extensions=["tables"])
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	with open(out_path, "w", encoding="utf-8") as f:
		f.write(f'<!DOCTYPE html>\n<html lang="{lang}"><head><meta charset="utf-8"><title>TermAssist</title></head><body>\n{body}\n</body></html>\n')


def version():
	with open(os.path.join(ADDON, "manifest.ini"), encoding="utf-8") as f:
		for line in f:
			if line.startswith("version"):
				return line.split("=", 1)[1].strip()


def main():
	import runpy
	runpy.run_path(os.path.join(ROOT, "tools", "i18n_extract.py"), run_name="__main__")
	html(os.path.join(ROOT, "docs", "readme.th.md"), os.path.join(ADDON, "doc", "th", "readme.html"), "th")
	html(os.path.join(ROOT, "docs", "readme.en.md"), os.path.join(ADDON, "doc", "en", "readme.html"), "en")
	out = os.path.join(ROOT, f"termAssist-{version()}.nvda-addon")
	with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
		for d, _dirs, files in os.walk(ADDON):
			if "__pycache__" in d:
				continue
			for fn in files:
				p = os.path.join(d, fn)
				z.write(p, os.path.relpath(p, ADDON))
	print(out)


if __name__ == "__main__":
	main()
