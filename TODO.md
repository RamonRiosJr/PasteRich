# PasteRich Development Backlog

## Core Daemon Improvements
- [ ] **Cross-Platform Installers:** Create `.msi` (Windows), `.dmg` (macOS), and `.deb` (Linux) installers.
- [ ] **Dynamic Theme Engine:** Allow users to swap Pygments CSS themes dynamically from the system tray instead of manually editing `config.json`.
- [ ] **Telemetry (Opt-In):** Add a strictly opt-in feature to send crash reports via Odoo XML-RPC.

## Future Official Plugins
- [ ] **Odoo XML-RPC Integration:** A plugin that allows users to highlight text, hit `Ctrl+Shift+T`, and instantly create a Helpdesk ticket or CRM Lead directly in their remote Odoo instance.
- [ ] **Jira / Linear Integration:** Instantly convert markdown into Jira/Linear tickets.
- [ ] **LLM Translate (F11):** An AI plugin that translates highlighted clipboard text into a target language before pasting as RTF.

## Documentation
- [ ] **Plugin Development Guide:** Write a detailed guide on how external developers can build and submit their own plugins to the `plugins/` architecture.
