# TermAssist — configuration spec.
# Registered as soon as this module is imported, before anything reads config.conf["termAssist"].
# NVDA caches a missing key, so reading the section before the spec exists would make it
# unreadable for the rest of the session (KeyError: 'termAssist').
import config

SECTION = "termAssist"
confspec = {
	"language": 'option("auto", "th", "en", default="auto")',
	"announceDone": "boolean(default=True)",
	"speakLineCount": "boolean(default=False)",
	"notifyBackground": "boolean(default=True)",
	"errorSound": "boolean(default=True)",
	"passwordGuard": "boolean(default=True)",
	"sendMethod": 'option("paste", "type", default="paste")',
	"clearLineKeys": 'string(default="control+e,control+u")',
	"promptRegex": 'string(default="")',
	"pollInterval": "integer(default=400, min=150, max=2000)",
	"historySize": "integer(default=5000, min=500, max=50000)",
	"profileAnnounce": "boolean(default=True)",
	"extraApps": 'string(default="mobaxterm")',
}


def register():
	if SECTION not in config.conf.spec:
		config.conf.spec[SECTION] = confspec


register()
