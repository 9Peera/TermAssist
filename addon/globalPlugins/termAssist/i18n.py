# TermAssist — translation helper.
# Strings are written as tr(english, thai).
# - Thai (setting "th", or NVDA in Thai with setting "auto"): the Thai text.
# - English forced: the English text.
# - Any other NVDA language: NVDA's gettext translation of the English text (locale/<lang>/LC_MESSAGES/nvda.po),
#   so community translators can add languages the standard way.
import addonHandler
import languageHandler

try:
	addonHandler.initTranslation()  # defines _ in this module
except Exception:  # pragma: no cover - outside NVDA
	pass
_gettext = globals().get("_", lambda s: s)


def _nvdaLang():
	try:
		return languageHandler.getLanguage().lower()
	except Exception:
		return "en"


def lang():
	try:
		import config
		pref = config.conf["termAssist"]["language"]
		if pref in ("th", "en"):
			return pref
	except Exception:
		pass
	return "th" if _nvdaLang().startswith("th") else "en"


def tr(en, th):
	l = lang()
	if l == "th":
		return th
	try:
		import config
		forced = config.conf["termAssist"]["language"] == "en"
	except Exception:
		forced = False
	if forced or _nvdaLang().startswith("en"):
		return en
	return _gettext(en)
