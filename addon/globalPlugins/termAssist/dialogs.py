# TermAssist — dialogs: edit command, compose, command library
# Author: Peera Pilarit
import ui
import wx
from gui import guiHelper

from . import library
from .i18n import lang, tr

RISK_TEXT = {
	"low": ("low", "ต่ำ"),
	"medium": ("medium — changes the system", "ปานกลาง — มีการเปลี่ยนแปลงระบบ"),
	"high": ("HIGH — may delete data or cut the connection", "สูง — อาจลบข้อมูลหรือตัดการเชื่อมต่อ"),
}


def _finish(dlg, sHelper, bHelper):
	sHelper.addDialogDismissButtons(bHelper)
	main = wx.BoxSizer(wx.VERTICAL)
	main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND)
	main.Fit(dlg)
	dlg.SetSizer(main)
	dlg.CentreOnScreen()


class EditCommandDialog(wx.Dialog):
	"""Edit the current command line in a normal Windows edit field."""

	def __init__(self, parent, command):
		super().__init__(parent, title=tr("TermAssist — Edit command", "TermAssist — แก้ไขคำสั่ง"))
		self.action = None
		s = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.text = s.addLabeledControl(tr("&Command:", "&คำสั่ง:"), wx.TextCtrl, size=(560, -1))
		self.text.SetValue(command)
		b = guiHelper.ButtonHelper(wx.HORIZONTAL)
		rep = b.addButton(self, label=tr("&Replace", "&แทนที่"))
		run = b.addButton(self, label=tr("Replace and r&un", "แทนที่และ&รัน"))
		cancel = b.addButton(self, id=wx.ID_CANCEL, label=tr("Cancel", "ยกเลิก"))
		rep.SetDefault()
		rep.Bind(wx.EVT_BUTTON, lambda e: self._done("replace"))
		run.Bind(wx.EVT_BUTTON, lambda e: self._done("run"))
		_finish(self, s, b)
		self.text.SetFocus()
		self.text.SetInsertionPointEnd()

	def _done(self, action):
		self.action = action
		self.value = self.text.GetValue()
		self.EndModal(wx.ID_OK)


class ComposeDialog(wx.Dialog):
	"""Write multi-line text, then send it as commands or write it to a file (heredoc)."""

	def __init__(self, parent):
		super().__init__(parent, title=tr("TermAssist — Compose text", "TermAssist — เขียนข้อความหลายบรรทัด"))
		self.result = None
		s = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.text = s.addLabeledControl(tr("&Text:", "&ข้อความ:"), wx.TextCtrl, style=wx.TE_MULTILINE, size=(560, 260))
		self.mode = s.addItem(wx.RadioBox(
			self, label=tr("Send as", "ส่งเป็น"), majorDimension=1, style=wx.RA_SPECIFY_COLS,
			choices=[
				tr("&Commands (each line is a command)", "&คำสั่ง (แต่ละบรรทัดคือหนึ่งคำสั่ง)"),
				tr("Content of a &file", "เนื้อหาของ&ไฟล์"),
			],
		))
		self.path = s.addLabeledControl(tr("File &path:", "&ตำแหน่งไฟล์:"), wx.TextCtrl)
		self.sudo = s.addItem(wx.CheckBox(self, label=tr("Use &sudo (system file)", "ใช้ &sudo (ไฟล์ระบบ)")))
		self.append = s.addItem(wx.CheckBox(self, label=tr("&Append to the end of the file", "&ต่อท้ายไฟล์เดิม")))
		self.enter = s.addItem(wx.CheckBox(self, label=tr("Press &Enter after sending", "กด &Enter หลังส่ง")))
		self.enter.SetValue(True)
		b = guiHelper.ButtonHelper(wx.HORIZONTAL)
		ok = b.addButton(self, label=tr("Se&nd", "&ส่ง"))
		b.addButton(self, id=wx.ID_CANCEL, label=tr("Cancel", "ยกเลิก"))
		ok.Bind(wx.EVT_BUTTON, self._onSend)
		self.mode.Bind(wx.EVT_RADIOBOX, lambda e: self._sync())
		_finish(self, s, b)
		self._sync()
		self.text.SetFocus()

	def _sync(self):
		isFile = self.mode.GetSelection() == 1
		for c in (self.path, self.sudo, self.append):
			c.Enable(isFile)

	def _onSend(self, evt):
		content = self.text.GetValue()
		if not content.strip():
			wx.Bell()
			self.text.SetFocus()
			return
		if self.mode.GetSelection() == 1:
			path = self.path.GetValue().strip()
			if not path:
				wx.Bell()
				self.path.SetFocus()
				return
			text = library.buildHeredoc(content, path, self.sudo.GetValue(), self.append.GetValue())
			enter = True
		else:
			text = content.replace("\r\n", "\n").rstrip("\n")
			enter = self.enter.GetValue()
		self.result = (text, enter)
		self.EndModal(wx.ID_OK)


class PaletteDialog(wx.Dialog):
	"""Searchable bilingual command library. Returns (command, action); parameters are filled by the plugin."""

	def __init__(self, parent, lib, store, host=None, query="", catId=None):
		super().__init__(parent, title=tr("TermAssist — Command library", "TermAssist — คลังคำสั่ง"))
		self.lib = lib
		self.store = store
		self.host = host
		self.lang = lang()
		self.result = None  # (command or None, action)
		self.items = []
		detected = store.detected(host) or []
		cats = lib.orderedCategories(detected)
		s = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.search = s.addLabeledControl(tr("&Search (Thai or English):", "&ค้นหา (ไทยหรืออังกฤษ):"), wx.TextCtrl, size=(560, -1))
		self.catIds = [None, library.FAVORITES, library.RECENT] + [c["id"] for c in cats]
		mark = tr(" (installed)", " (มีในเครื่อง)")
		catNames = [tr("All categories", "ทุกหมวด"), tr("Favorites", "รายการโปรด"), tr("Recently used", "ใช้ล่าสุด")]
		catNames += [lib.categoryName(c["id"], self.lang) + (mark if c["id"] in detected else "") for c in cats]
		self.cat = s.addLabeledControl(tr("Cate&gory:", "ห&มวด:"), wx.Choice, choices=catNames)
		self.cat.SetSelection(self.catIds.index(catId) if catId in self.catIds else 0)
		self.list = s.addLabeledControl(tr("C&ommands:", "คำ&สั่ง:"), wx.ListBox, size=(560, 260))
		self.detail = s.addLabeledControl(
			tr("&Details:", "&รายละเอียด:"), wx.TextCtrl, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(560, 110)
		)
		b = guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.insertBtn = b.addButton(self, label=tr("&Insert", "แ&ทรก"))
		self.runBtn = b.addButton(self, label=tr("&Run", "&รัน"))
		self.copyBtn = b.addButton(self, label=tr("&Copy", "&คัดลอก"))
		self.favBtn = b.addButton(self, label=tr("Add to &favorites", "เพิ่มใน&รายการโปรด"))
		self.addBtn = b.addButton(self, label=tr("&New command...", "เพิ่มคำสั่ง&ใหม่..."))
		self.delBtn = b.addButton(self, label=tr("De&lete", "&ลบ"))
		self.detectBtn = b.addButton(self, label=tr("Detect ser&vices", "ตรวจหา&บริการในเครื่อง"))
		b.addButton(self, id=wx.ID_CANCEL, label=tr("Close", "ปิด"))
		self.insertBtn.SetDefault()
		self.insertBtn.Bind(wx.EVT_BUTTON, lambda e: self._act("insert"))
		self.runBtn.Bind(wx.EVT_BUTTON, lambda e: self._act("run"))
		self.copyBtn.Bind(wx.EVT_BUTTON, lambda e: self._act("copy"))
		self.favBtn.Bind(wx.EVT_BUTTON, self._onFav)
		self.addBtn.Bind(wx.EVT_BUTTON, self._onAdd)
		self.delBtn.Bind(wx.EVT_BUTTON, self._onDelete)
		self.detectBtn.Bind(wx.EVT_BUTTON, self._onDetect)
		self.search.Bind(wx.EVT_TEXT, lambda e: self._refresh())
		self.search.Bind(wx.EVT_KEY_DOWN, self._onSearchKey)
		self.cat.Bind(wx.EVT_CHOICE, lambda e: self._refresh())
		self.list.Bind(wx.EVT_LISTBOX, lambda e: self._showDetail())
		self.list.Bind(wx.EVT_LISTBOX_DCLICK, lambda e: self._act("insert"))
		_finish(self, s, b)
		if query:
			self.search.ChangeValue(query)
		self._refresh()
		self.search.SetFocus()

	# ---- list handling
	def _refresh(self):
		self.items = self.lib.search(self.search.GetValue(), self.catIds[self.cat.GetSelection()])
		labels = []
		for c in self.items:
			star = "★ " if self.store.isFavorite(c.id) else ""
			group = f"{self.lib.groupName(c.group, self.lang)}: " if c.group else ""
			labels.append(f"{star}{group}{c.label(self.lang)} — {c.template}")
		self.list.Set(labels)
		if labels:
			self.list.SetSelection(0)
		self._showDetail()

	def _onSearchKey(self, evt):
		if evt.GetKeyCode() in (wx.WXK_DOWN, wx.WXK_UP) and self.items:
			self.list.SetFocus()
		else:
			evt.Skip()

	def _selected(self):
		i = self.list.GetSelection()
		return self.items[i] if 0 <= i < len(self.items) else None

	def _showDetail(self):
		c = self._selected()
		if not c:
			self.detail.SetValue(tr("No matching commands.", "ไม่พบคำสั่งที่ตรงกัน"))
			for btn in (self.insertBtn, self.runBtn, self.copyBtn, self.favBtn, self.delBtn):
				btn.Enable(False)
			return
		for btn in (self.insertBtn, self.runBtn, self.copyBtn, self.favBtn):
			btn.Enable(True)
		self.delBtn.Enable(c.custom)
		th = self.lang == "th"
		risk = RISK_TEXT.get(c.risk, RISK_TEXT["low"])[1 if th else 0]
		cat = self.lib.categoryName(c.cat, self.lang)
		if c.group:
			cat += " / " + self.lib.groupName(c.group, self.lang)
		lines = [
			c.label(self.lang),
			tr("Command: ", "คำสั่ง: ") + c.template,
			tr("Category: ", "หมวด: ") + cat,
			tr("Risk: ", "ความเสี่ยง: ") + risk,
		]
		params = c.paramNames()
		if params:
			parts = []
			for p in params:
				label = self.lib.paramLabel(p, self.lang)
				if self.lib.paramSource(p):
					label += tr(" (list from server)", " (เลือกจากเซิร์ฟเวอร์ได้)")
				parts.append(label)
			lines.append(tr("You will be asked for: ", "จะถามค่า: ") + ", ".join(parts))
		if not c.sr:
			lines.append(tr("Note: full-screen program, harder to read with a screen reader.", "หมายเหตุ: เป็นโปรแกรมเต็มจอ อ่านด้วยโปรแกรมอ่านหน้าจอได้ยากกว่า"))
		if c.description(self.lang):
			lines.append(c.description(self.lang))
		self.detail.SetValue("\n".join(lines))
		self.favBtn.SetLabel(
			tr("Remove from &favorites", "นำออกจาก&รายการโปรด") if self.store.isFavorite(c.id) else tr("Add to &favorites", "เพิ่มใน&รายการโปรด")
		)

	# ---- actions
	def _act(self, action):
		c = self._selected()
		if not c:
			wx.Bell()
			return
		self.result = (c, action)
		self.EndModal(wx.ID_OK)

	def _onDetect(self, evt):
		self.result = (None, "detect")
		self.EndModal(wx.ID_OK)

	def _onFav(self, evt):
		c = self._selected()
		if not c:
			return
		added = self.store.toggleFavorite(c.id)
		ui.message(tr("Added to favorites", "เพิ่มในรายการโปรดแล้ว") if added else tr("Removed from favorites", "นำออกจากรายการโปรดแล้ว"))
		sel = self.list.GetSelection()
		self._refresh()
		if 0 <= sel < self.list.GetCount():
			self.list.SetSelection(sel)
			self._showDetail()

	def _onAdd(self, evt):
		name = wx.GetTextFromUser(tr("Name of the command:", "ชื่อคำสั่ง:"), tr("New command", "เพิ่มคำสั่งใหม่"), parent=self)
		if not name.strip():
			return
		tpl = wx.GetTextFromUser(
			tr("Command (use {name} for values to ask, e.g. {file}):", "คำสั่ง (ใช้ {ชื่อ} สำหรับค่าที่ต้องถาม เช่น {file}):"),
			tr("New command", "เพิ่มคำสั่งใหม่"), parent=self,
		)
		if not tpl.strip():
			return
		self.store.addCustom(name.strip(), tpl.strip())
		self.lib.reloadCustom()
		self.cat.SetSelection(self.catIds.index(library.CUSTOM))
		self.search.SetValue("")
		self._refresh()
		self.list.SetFocus()

	def _onDelete(self, evt):
		c = self._selected()
		if not c or not c.custom:
			return
		if wx.MessageBox(
			tr(f"Delete '{c.label(self.lang)}'?", f"ลบ '{c.label(self.lang)}' หรือไม่"),
			tr("Confirm", "ยืนยัน"), wx.YES_NO | wx.NO_DEFAULT, self,
		) != wx.YES:
			return
		self.store.removeCustom(c.id)
		self.lib.reloadCustom()
		self._refresh()
		self.list.SetFocus()
