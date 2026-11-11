# TermAssist — terminal assistant

* Author: Peera Pilarit
* Version: 1.0.1
* NVDA compatibility: 2026.1 and later (tested with 2026.3)
* Source code and issues: https://github.com/9Peera/termAssist

TermAssist makes working on Linux servers (such as Ubuntu) through a terminal program easier with NVDA: reading output, typing and editing commands, and finding common commands in a searchable Thai/English command library.

## Supported programs

* PuTTY, KiTTY, PuTTYtel
* PuTTY embedded in MTPuTTY and SuperPuTTY
* Windows Terminal and the Windows console (cmd, PowerShell), for example with `ssh`
* MobaXterm and other programs added in the settings (experimental)

## Getting started

### Interface language

The add-on follows NVDA's language. To choose a language yourself:

1. Press NVDA+Control+G to open NVDA Settings.
2. Select the **TermAssist** category.
3. In **Language / ภาษา**, choose Follow NVDA, Thai or English, then press **OK**.

### PuTTY character set

For correct non-English text, open PuTTY, go to **Window > Translation**, set **Remote character set** to **UTF-8**, then save **Default Settings** in the **Session** category.

## Command layer

In a terminal press **NVDA+Control+Shift+P** (a short beep), release all keys, then press one key:

| Key | Action |
|---|---|
| H | List all layer keys |
| 1 – 9 | Read the 1st–9th line above the prompt |
| Shift+1 – 9 | Copy that line |
| L | Summary of the last command (lines, lines that look like errors) |
| O | View output of the last command |
| Shift+O | View the whole history |
| R | Read the command typed so far |
| E | Edit the current command line in a normal edit field |
| M | Compose multi-line text or write a file |
| C | Command library |
| S | Session information (user, host, folder) |
| P | Status of nano, vim, pager, top, htop |
| T / B | Read the top / bottom line of the screen |
| A | Toggle the command-finished sound |
| D | Diagnostics report (copied to the clipboard) |
| Esc | Leave the layer |

Any other key leaves the layer with a low tone. Every command can also be given a direct gesture in NVDA menu > Preferences > Input gestures > TermAssist.

## Sounds and automatic announcements

* **Short high beep:** a command finished. If the terminal is in the background, this is also spoken.
* **Low tone:** the output contains an error (error, failed, denied, not found, …).
* **Two-tone beep:** password prompt. Typed characters are muted until the prompt is gone.
* **Full-screen programs:**
  * nano status messages such as `[ Wrote 12 lines ]` are read.
  * vim mode changes are announced.
  * The end of the document in less/man is announced.

## Edit command (E)

Type a command without pressing Enter, then press E. Edit it in a normal edit field, then choose **Replace** or **Replace and run**.

## Compose (M)

* **Commands:** each line is a command, and all of them are run.
* **Content of a file:** enter a path. Optionally use sudo for system files, or append to the file instead of overwriting it.

## Command library (C)

The library has 163 basic commands in 15 categories plus 13 service packs.

1. Search in Thai or English, then press Down Arrow to reach the list.
2. The details show the real command, its category, its risk level and the values it will ask for.
3. Choose **Insert** (Enter), **Run** or **Copy**.

**Values from the server:** when a value can be listed (services, containers, sites, databases, files, users, branches, …), leave it blank and press OK. A list is fetched from the server for you to choose from.

* The terminal must be at a prompt.
* If the list is empty, the reason is given: not installed, no such folder, permission denied, service not running, or simply empty.

**Safety:**

* High-risk commands ask for confirmation before running.
* A command is never sent with an empty value.

**Service packs:** Docker/Compose, Nginx, Apache, MySQL/MariaDB, PostgreSQL, PHP/PHP-FPM, Redis, Certbot, Git, Node.js/PM2, Python/venv, Fail2ban, Samba.

* Each pack has the same groups: installed, status, control, logs, test, config, tasks, troubleshooting.
* Installed services are detected automatically the first time you use a pack on a host, or with **Detect services**.
* If a service is missing, you are offered to install it.

Favorites, recently used and your own commands are stored in `termAssist.json` in NVDA's configuration folder.

## Notes

* When text is pasted, the clipboard is used briefly and restored after about a second.
* Full-screen programs are not recorded in the history.
* In Windows Terminal only the visible lines are read.
* Explaining why a list is empty needs bash, which is the default shell on Ubuntu.

## Reporting problems

Press NVDA+Control+Shift+P then D. Then open an issue at https://github.com/9Peera/termAssist/issues with the report and the steps you took.
