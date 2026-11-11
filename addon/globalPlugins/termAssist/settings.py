# TermAssist — configuration and NVDA settings panel
# Author: Peera Pilarit
import config
import wx
from gui import guiHelper, nvdaControls
from gui.settingsDialogs import SettingsPanel

from . import prompt
from .i18n import tr

from .confspec import SECTION, confspec, register


def init():
	register()


def conf():
	return config.conf[SECTION]


def extraApps():
	return {a.strip().lower() for a in conf()["extraApps"].split(",") if a.strip()}


class TermAssistPanel(SettingsPanel):
	title = "TermAssist"

	def makeSettings(self, settingsSizer):
		h = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		c = conf()
		self.langs = ["auto", "th", "en"]
		# Label is always bilingual so it can be found whatever the current language is.
		self.lang = h.addLabeledControl(
			"&Language / ภาษา:", wx.Choice,
			choices=["Follow NVDA / ตาม NVDA", "ไทย (Thai)", "English (อังกฤษ)"],
		)
		self.lang.SetSelection(self.langs.index(c["language"]))
		self.chk = {}
		for key, label in (
			("announceDone", tr("Beep when a command &finishes", "ส่งเสียงเมื่อคำสั่ง&ทำงานเสร็จ")),
			("speakLineCount", tr("Speak the number of output &lines when done", "บอก&จำนวนบรรทัดผลลัพธ์เมื่อเสร็จ")),
			("notifyBackground", tr("Announce when a command finishes in a terminal that is &not focused", "แจ้งเมื่อคำสั่งเสร็จในเทอร์มินัลที่&ไม่ได้โฟกัสอยู่")),
			("errorSound", tr("Play a sound when the output contains an &error", "ส่งเสียงเมื่อพบ&ข้อผิดพลาดในผลลัพธ์")),
			("passwordGuard", tr("Mute typed characters at &password prompts", "ปิดเสียงอ่านตัวอักษรที่พิมพ์เมื่อป้อน&รหัสผ่าน")),
			("profileAnnounce", tr("Announce nano, vim and pager &status changes", "บอก&สถานะของ nano, vim และโหมดอ่านทีละหน้า")),
		):
			cb = h.addItem(wx.CheckBox(self, label=label))
			cb.SetValue(c[key])
			self.chk[key] = cb
		self.methods = ["paste", "type"]
		self.method = h.addLabeledControl(
			tr("&Method for sending text:", "วิธี&ส่งข้อความเข้าเทอร์มินัล:"),
			wx.Choice,
			choices=[
				tr("Paste through the clipboard (Shift+Insert)", "วางผ่านคลิปบอร์ด (Shift+Insert)"),
				tr("Type characters directly (PuTTY family only)", "พิมพ์ตัวอักษรโดยตรง (เฉพาะกลุ่ม PuTTY)"),
			],
		)
		self.method.SetSelection(self.methods.index(c["sendMethod"]))
		self.clearKeys = h.addLabeledControl(tr("&Keys that clear the command line:", "ปุ่มที่ใช้&ล้างบรรทัดคำสั่ง:"), wx.TextCtrl)
		self.clearKeys.SetValue(c["clearLineKeys"])
		self.promptRe = h.addLabeledControl(
			tr("Custom prompt &regular expression (empty = default):", "&Regex ของ prompt แบบกำหนดเอง (ว่าง = ค่าเริ่มต้น):"), wx.TextCtrl
		)
		self.promptRe.SetValue(c["promptRegex"])
		self.extraApps = h.addLabeledControl(
			tr("Other terminal programs, experimental (app names, comma separated):", "โปรแกรมเทอร์มินัลอื่น แบบทดลอง (ชื่อแอป คั่นด้วยจุลภาค):"), wx.TextCtrl
		)
		self.extraApps.SetValue(c["extraApps"])
		self.poll = h.addLabeledControl(
			tr("Check the screen every (&milliseconds):", "ตรวจหน้าจอทุก ๆ (&มิลลิวินาที):"),
			nvdaControls.SelectOnFocusSpinCtrl, min=150, max=2000, initial=c["pollInterval"],
		)
		self.hist = h.addLabeledControl(
			tr("&History size (lines):", "ขนาด&ประวัติ (บรรทัด):"),
			nvdaControls.SelectOnFocusSpinCtrl, min=500, max=50000, initial=c["historySize"],
		)

	def isValid(self):
		pat = self.promptRe.GetValue().strip()
		if pat and not prompt.isValidPattern(pat):
			wx.MessageBox(
				tr("The prompt regular expression is not valid.", "Regex ของ prompt ไม่ถูกต้อง"),
				"TermAssist", wx.OK | wx.ICON_ERROR, self,
			)
			return False
		return super().isValid()

	def onSave(self):
		c = conf()
		c["language"] = self.langs[self.lang.GetSelection()]
		for key, cb in self.chk.items():
			c[key] = cb.GetValue()
		c["sendMethod"] = self.methods[self.method.GetSelection()]
		c["clearLineKeys"] = self.clearKeys.GetValue().strip()
		c["promptRegex"] = self.promptRe.GetValue().strip()
		c["pollInterval"] = self.poll.GetValue()
		c["extraApps"] = self.extraApps.GetValue().strip()
		c["historySize"] = self.hist.GetValue()
