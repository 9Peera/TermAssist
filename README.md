# TermAssist — NVDA add-on for terminals / ผู้ช่วยเทอร์มินัลสำหรับ NVDA

TermAssist makes PuTTY, KiTTY, Windows Terminal and the Windows console easier to use with the NVDA screen reader when working on Linux servers.

TermAssist ช่วยให้ใช้ PuTTY, KiTTY, Windows Terminal และคอนโซลของ Windows กับโปรแกรมอ่านหน้าจอ NVDA ได้สะดวกขึ้นเมื่อทำงานกับเซิร์ฟเวอร์ Linux

* Requires NVDA 2026.1 or later / ใช้กับ NVDA 2026.1 ขึ้นไป
* Install from the NVDA Add-on Store, or download the `.nvda-addon` file from [Releases](https://github.com/9Peera/termAssist/releases)
* User guide: [English](docs/readme.en.md) · [ภาษาไทย](docs/readme.th.md)

## Features / ความสามารถ

* Sounds when a command finishes or prints an error; spoken notice for background terminals
* Read or copy the last lines, view the last output or the whole history
* Edit the command line in a normal edit field; compose multi-line text or write files (with sudo)
* Mutes typed characters at password prompts
* nano, vim, less/man, top and htop announcements
* Bilingual (Thai/English) command library: 163 Ubuntu commands in 15 categories plus 13 service packs (Docker, Nginx, Apache, MySQL/MariaDB, PostgreSQL, PHP-FPM, Redis, Certbot, Git, Node.js/PM2, Python, Fail2ban, Samba)
* Values such as service, container, site or database names can be picked from a list fetched from the server

Press **NVDA+Control+Shift+P** in a terminal, then **H** for help.

## Building / การสร้างไฟล์ติดตั้ง

```
pip install -r requirements-dev.txt
python tools/build_commands.py     # core command library
python tools/build_packs.py        # service packs
python tools/build.py              # translations, docs and termAssist-<version>.nvda-addon
python tests/test_core.py          # logic tests
python tests/smoke_nvda_stubs.py   # plugin smoke test with stubbed NVDA modules
```

## Translating / การแปล

Strings are extracted to `nvda.pot` by `tools/i18n_extract.py`. Add `addon/locale/<lang>/LC_MESSAGES/nvda.po` for a new language.

## License / สัญญาอนุญาต

GNU General Public License version 2. See [LICENSE](LICENSE).

Copyright (C) 2026 Peera Pilarit
