# TermAssist — output history tracker (pure Python, no NVDA imports)
# Author: Peera Pilarit
from collections import deque


def newLines(old, new):
	"""Lines in `new` that were not on screen in `old`.
	Uses the largest overlap where the end of old == the start of new (screen scroll)."""
	if old == new:
		return []
	if not old:
		return list(new)
	n = min(len(old), len(new))
	for k in range(n, 0, -1):
		if old[-k:] == new[:k]:
			return list(new[k:])
	return None  # no overlap: clear screen, redraw or very fast output


class OutputTracker:
	"""Keeps a history of committed terminal lines.
	The last screen line (cursor / prompt line) is never committed until it scrolls up."""

	REDRAW_STREAK = 2  # consecutive unmatched snapshots => full-screen app, stop recording

	def __init__(self, maxLines=5000):
		self._hist = deque(maxlen=maxLines)
		self.total = 0
		self._prev = None
		self._unmatched = 0

	def resize(self, maxLines):
		if maxLines != self._hist.maxlen:
			self._hist = deque(self._hist, maxlen=maxLines)

	def update(self, lines):
		if not lines:
			return []
		stable = list(lines[:-1])
		if self._prev is None:
			new = stable
		else:
			new = newLines(self._prev, stable)
			if new is None:
				self._unmatched += 1
				new = stable if self._unmatched < self.REDRAW_STREAK else []
			else:
				self._unmatched = 0
		self._prev = stable
		for line in new:
			self._hist.append((self.total, line))
			self.total += 1
		return new

	@property
	def inFullScreenMode(self):
		return self._unmatched >= self.REDRAW_STREAK

	def since(self, index):
		return [l for i, l in self._hist if i >= index]

	def all(self):
		return [l for _, l in self._hist]

	def clear(self):
		self._hist.clear()
