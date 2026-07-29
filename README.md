<div align="center">
  <img src="assets/icon.png" width="128" height="128" alt="PasteRich Logo">
  <h1>PasteRich</h1>
  <p><b>A lightweight, cross-platform background daemon for converting raw Markdown to Rich Text on the fly.</b></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
  [![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)](#)
  [![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
</div>

---

## ⚡ Overview

**PasteRich** solves a massive friction point for developers: copying Markdown documentation, snippets, or AI outputs, and needing to paste them into enterprise applications (Microsoft Word, Outlook, Teams, Google Docs) without losing formatting.

Instead of running a heavy Electron application, PasteRich operates as an ultra-lightweight background system daemon. Copy any raw markdown text, hit your global hotkey, and PasteRich will instantly convert it to HTML/RTF, inject it into your OS clipboard, and seamlessly paste it directly into your active window.

---

## ✨ Features

- 🖥️ **Cross-Platform Native Clipboards:** Supports Windows (`CF_HTML`), macOS (`NSPasteboard` via RTF), and Linux (`xclip`/`xsel`).
- 🪶 **Zero-Overhead Daemon:** Runs silently in the system tray. Absolutely no heavy frontend frameworks.
- ⌨️ **Dynamic Hotkey GUI:** Change your global shortcut instantly via a native UI popup. No app restarts required!
- 🔄 **Auto-Updates:** Built-in update checker directly from GitHub releases with seamless one-click downloads.
- 🚀 **First-Run Welcome Screen:** Clean UI on first launch showing your current hotkey and instructions.
- 🚀 **Auto-Start:** Built-in support to register itself to run on system boot.
- 🎨 **Smart CSS Styling:** Uses GitHub's aesthetic for tables, blockquotes, and text.
- 🧑‍💻 **Code Highlighting:** Full syntax highlighting for code blocks via Pygments (Defaults to `Monokai`).
- 🧠 **Smart Pass-Through:** If the clipboard doesn't contain Markdown, the hotkey acts exactly like a normal paste!

---

## 🚀 Installation & Usage

The easiest way to use PasteRich is to download the standalone compiled executable from the **[Releases](#)** page. No installation required!

### 1. Run the Executable
Launch `PasteRich`. A purple clipboard icon will appear in your system tray/menu bar.

### 2. Copy Markdown
Copy any text containing Markdown elements (e.g. `**bold**`, `# headers`, or ` ```python `).

### 3. Hit the Hotkey!
Switch to your target application (Word, Outlook, etc.) and press the global hotkey:
*   **Windows & Linux:** `F8` (Default)
*   **macOS:** `F8` (Default)

The markdown will be rendered as beautiful rich text instantly!

---

## ⚙️ Configuration

You can dynamically change your hotkey by **right-clicking the tray icon** and selecting **Change Hotkey**. You can also manually **Check for Updates** or **Refresh Hotkey** from this menu. 

For advanced configuration, PasteRich creates a `config.json` in the same directory as the executable.

```json
{
    "hotkey": "f8",
    "theme": "monokai"
}
```

### Custom Styling (`style.css`)
Want to customize how your pasted tables, fonts, or blockquotes look? Simply create a file named `style.css` in the same directory as `PasteRich`. If detected, PasteRich will automatically use your custom CSS instead of the default GitHub theme!

---

## 🛠️ Building from Source

If you want to compile the executable yourself, PasteRich is built entirely in Python using `PyInstaller`.

1. Clone the repository and setup your environment:
```bash
git clone https://github.com/RamonRiosJr/PasteRich.git
cd PasteRich
python -m venv venv
```

2. Activate the virtual environment:
*   **Windows:** `.\venv\Scripts\activate`
*   **macOS/Linux:** `source venv/bin/activate`

3. Install requirements and compile:
```bash
pip install -r requirements.txt
python build.py
```
The compiled, standalone binary will be generated in the `/dist` directory.

---

## 🤝 Contributing & Architecture
PasteRich is written in strictly-typed Python (`pasterich.py`). We welcome pull requests for new themes, extended markdown support, or OS-specific optimizations!

## 📜 License
Distributed under the **MIT License**. See `LICENSE` for more information.
