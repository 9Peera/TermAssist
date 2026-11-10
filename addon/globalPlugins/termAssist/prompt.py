# TermAssist — prompt / password / error detection (pure Python, no NVDA imports)
# Author: Peera Pilarit
import re

# Matches common shell prompts. Named groups: prompt, cmd (cmd may be None).
#  user@host:~$ ls      root@srv:/etc#      [user@host dir]$      (venv) user@h:~/p$
#  PS C:\Users\x>       C:\Windows>         mysql>   MariaDB [db]>   postgres=#
DEFAULT_PROMPT = (
	r"^(?P<prompt>"
	r"(?:\([^)]*\)\s*)?\[?[\w.\-]+@[\w.\-]+[^$#\n]*?[$#]"
	r"|PS [^>\n]*>"
	r"|[A-Za-z]:\\[^>\n]*>"
	r"|(?:mysql|MariaDB \[[^\]]*\])>"
	r"|\w+=[#>]"
	r")(?:\s(?P<cmd>.*))?$"
)

PASSWORD_RE = re.compile(
	r"(?i)(?:password|passphrase|passcode|รหัสผ่าน)[^:：\n]*[:：]\s*$"
)

ERROR_RE = re.compile(
	r"(?i)(?:\b(?:error|failed|failure|fatal|denied|cannot|unable to|not found|"
	r"no such file|segmentation fault|traceback|refused)\b|^E: )"
)

SESSION_RE = re.compile(
	r"(?P<user>[\w.\-]+)@(?P<host>[\w.\-]+)(?:[: ](?P<path>[^\s$#\]]*))?"
)


class PromptDetector:
	def __init__(self, pattern=""):
		self.pattern = pattern or DEFAULT_PROMPT
		try:
			self._re = re.compile(self.pattern)
		except re.error:
			self.pattern = DEFAULT_PROMPT
			self._re = re.compile(DEFAULT_PROMPT)

	def match(self, line):
		if not line:
			return None
		return self._re.match(line.strip())

	def isIdlePrompt(self, line):
		m = self.match(line)
		if not m:
			return False
		return not (m.groupdict().get("cmd") or "").strip()

	def split(self, line):
		"""Return (promptText or None, commandText)."""
		m = self.match(line)
		if not m:
			return None, (line or "").strip()
		return m.group("prompt"), (m.groupdict().get("cmd") or "").strip()


def isValidPattern(pattern):
	try:
		re.compile(pattern)
		return True
	except re.error:
		return False


def isPasswordPrompt(line):
	return bool(line) and bool(PASSWORD_RE.search(line.rstrip()))


def hasError(lines):
	return any(ERROR_RE.search(l) for l in lines)


def countErrors(lines):
	return sum(1 for l in lines if ERROR_RE.search(l))


def parseSession(promptText):
	m = SESSION_RE.search(promptText or "")
	if not m:
		return None
	return m.group("user"), m.group("host"), (m.group("path") or "")
