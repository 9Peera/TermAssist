# Changelog

## 1.0.1 — 2026-11-11

* Fixed: the add-on failed to start with `KeyError: 'termAssist'` when NVDA's configuration had no TermAssist section yet (for example after a fresh install or a configuration reset). The configuration section is now registered before anything reads it.
* Added a regression test that mimics NVDA's configuration cache.

## 1.0.0 — 2026-11-10

First public release.

* Terminal support: PuTTY family (incl. MTPuTTY/SuperPuTTY), Windows Terminal, Windows console; MobaXterm experimental.
* Command tracking: finished sound, error sound, background notification, last-command summary.
* Reading: lines 1–9 above the prompt, copy line, output viewer, history, top/bottom line, session info.
* Input: edit command line in a dialog, compose multi-line text, write files via heredoc (optional sudo/append).
* Password prompts mute typed-character echo.
* Full-screen profiles: nano, vim, less/man, top, htop.
* Command library: 163 core commands, 13 service packs, Thai/English search, parameters, values picked from the server, reasons for empty lists, high-risk confirmation, favorites, recent and custom commands, automatic service detection with install offer.
* Thai and English interface with a language setting; gettext template for other languages.
